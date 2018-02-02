import tkinter as tk
from tkinter import ttk
import matplotlib
import numpy as np
from utilities.helper_functions import fitFigToCanvas
from utilities.math_helpers import floatOrZero, floatOrNone
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import patches
import pickle

matplotlib.use("TkAgg")


class TimelinePage(ttk.Frame):
    name = 'Timeline'

    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.bind("<Visibility>", self.on_visibility)
        self.controller = controller
        self.gui = dict()
        self.gui['tFrame'] = TimelineStepsFrame(self, controller)
        self.gui['tFrame'].grid(row=0, column=0, columnspan=1)
        self.gui['f_timeline'] = self.controller.shared_figs['f_timeline']
        self.gui['canvas_timeline'] = FigureCanvasTkAgg(self.gui['f_timeline'], self)
        self.gui['canvas_timeline'].get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                                           highlightbackground='gray')
        self.gui['canvas_timeline'].show()
        self.gui['canvas_timeline'].get_tk_widget().grid(row=2, column=0, columnspan=2,
                                                         padx=10, pady=10, sticky='nsew')
        self.gui['timelineTableFrame'] = ttk.Frame(self)
        self.gui['timelineTableFrame'].grid(row=0, column=1, padx=10, pady=10)
        self.gui['timelineTree'] = ttk.Treeview(self.gui['timelineTableFrame'])
        self.gui['popup'] = tk.Menu(self, tearoff=0)
        self.create_timeline_table()
        self.draw_timeline_steps()

    def create_timeline_table(self):
        tree = self.gui['timelineTree']
        tree["columns"] = ("sn", "iu", 'ex', "p", "d")
        tree.column("#0", width=30)
        tree.column("sn", width=120)
        tree.column("iu", width=60)
        tree.column("ex", width=60)
        tree.column("p", width=60)
        tree.column("d", width=75)
        tree.heading("#0", text='#')
        tree.heading("sn", text="Step")
        tree.heading("iu", text="Type")
        tree.heading("ex", text="Exclusive")
        tree.heading("p", text="Period (s)")
        tree.heading("d", text="Duration (m)")
        tree.bind("<Button-3>", self.on_timeline_table_right_click)
        tree.bind("<<TreeviewSelect>>", self.on_timeline_table_select)
        tree.grid(row=0, column=0, sticky='nsew')
        scroll = ttk.Scrollbar(tree.master, orient="vertical", command=tree.yview)
        scroll.grid(row=0, column=1, sticky='nse', pady=10)
        tree.configure(yscrollcommand=scroll.set)

    def on_visibility(self, event):
        fitFigToCanvas(self.gui['f_timeline'], self.gui['canvas_timeline'],
                       self.controller.get_app_param('fig_dpi'))
        self.gui['canvas_timeline'].draw_idle()
        self.create_timeline_chart()

    def create_timeline_chart(self, *args):
        timeline_steps = self.controller.timelineSteps
        positions = self.controller.positions
        stagger = floatOrZero(self.gui['tFrame'].staggerEntryVar.get())

        if len(timeline_steps) == 0:
            return
        if len(positions) == 0:
            positions = {1: [], 2: [], 3: [], 4: [], 5: []}
        pos_timeline = {}
        ylabels1 = []
        ii = 0
        pos_ids = positions.keys()
        for posID in pos_ids:
            ylabels1.append('Position {0}'.format(posID))
            pos_timeline[posID] = []
            total_time = 0
            first_step = True
            for step in timeline_steps:
                if first_step:
                    start_time = 0
                    #                    D = step['D'] + min(stagger, step['D']) * ii
                    duration = step['D'] + stagger * ii
                    first_step = False
                else:
                    #                    start_time = stagger * ii + totalTime
                    start_time = total_time
                    duration = step['D']
                period = step['P']
                if duration is None or period is None:
                    duration = 1
                    period = 60
                if step['EX']:
                    period = duration * 60
                step_start_times = np.arange(start_time, start_time + duration, period / 60)
                step_end_times = step_start_times + period / 60
                step_start_end = np.array([step_start_times, step_end_times])
                pos_timeline[posID].append(np.array([step_start_end]))
                total_time += duration
            ii += 1

        backup = 0
        individual_steps = {}
        timeline_index = {}
        for posID in pos_ids:
            timeline_index[posID] = 0
            individual_steps[posID] = []
        min_time = np.zeros(len(pos_ids))
        while True:
            start_time = np.array([np.inf])
            for pos in pos_timeline:
                start_end = pos_timeline[pos][0][0][:, 0]  # figure out which thing is set to start next
                pos_ind = list(pos_ids).index(pos)
                _start = max(start_end[0], min_time[pos_ind])
                _end = _start + start_end[1] - start_end[0]
                exclusive = timeline_steps[timeline_index[pos]]['EX']
                if _start < start_time or (
                        _start == start_time and exclusive):  # figure out if this is the earliest step, or exclusive
                    #  step that starts the same time as others
                    start_time = _start
                    end_time = _end
                    first_pos = pos  # save which position runs first
            pos_ind = list(pos_ids).index(first_pos)
            exclusive = timeline_steps[timeline_index[first_pos]]['EX']

            individual_steps[first_pos].append({'start_time': start_time,
                                                'endTime': end_time,
                                                'EX': exclusive,
                                                'IU': timeline_steps[timeline_index[first_pos]]['IU']})
            # delete added position
            pos_timeline[first_pos][0] = np.array([np.delete(pos_timeline[first_pos][0][0], 0, 1)])
            if exclusive:
                min_time[min_time < end_time] = end_time
            else:
                min_time[pos_ind] = max(min_time[pos_ind], end_time)
                min_time[min_time < start_time] = start_time

            # if this step is done, move to next step
            if pos_timeline[first_pos][0].size == 0:
                timeline_index[first_pos] += 1
                del (pos_timeline[first_pos][0])
            # if this position is done, remove it
            if len(pos_timeline[first_pos]) == 0:
                del (pos_timeline[first_pos])
            if len(pos_timeline) == 0:
                break
            backup += 1
            if backup > 100000:  # make sure loop doesn't run forever while testing
                print('loop running too long')
                break

        self.controller.a_timeline.clear()
        y_ind = 0
        for key in individual_steps:
            yrange = (y_ind - .4, 0.8)
            xranges = []
            c = []
            y_ind += 1
            for step in individual_steps[key]:
                xranges.append((step['start_time'], step['endTime'] - step['start_time']))
                if not step['EX']:
                    c.append('blue')  # regular imaging
                elif step['EX'] and step['IU'] == 'Image':
                    c.append('green')  # exclusive imaging
                else:
                    c.append('red')  # uncaging
            self.controller.a_timeline.broken_barh(xranges, yrange, color=c, edgecolor='black')
        self.controller.a_timeline.set_yticks(list(range(len(pos_ids))))
        self.controller.a_timeline.set_yticklabels(ylabels1)
        self.controller.a_timeline.axis('tight')
        self.controller.a_timeline.set_ylim(auto=True)
        self.controller.a_timeline.grid(color='k', linestyle=':')
        y1, y2 = self.controller.a_timeline.get_ylim()
        if y2 > y1:
            self.controller.a_timeline.invert_yaxis()
        legend_patch_red = patches.Patch(color='red', label='Uncaging')
        legend_patch_blue = patches.Patch(color='blue', label='Imaging')
        legend_patch_green = patches.Patch(color='green', label='Exclusive Imaging')
        self.controller.a_timeline.legend(handles=[legend_patch_red, legend_patch_blue, legend_patch_green])
        self.controller.individualTimelineSteps = individual_steps
        self.gui['canvas_timeline'].draw_idle()

    #        app.frames[TimelinePage].canvas.draw_idle()

    def on_timeline_table_right_click(self, event):
        tree = self.gui['timelineTree']
        iid = tree.identify_row(event.y)
        if iid:
            # mouse over item
            tree.selection_set(iid)
        for item in tree.selection():
            item_text = tree.item(item, "text")
            item_number = tree.index(item)
            print(item_text)
            print(item_number)
        if len(tree.selection()) == 0:
            return
        self.gui['popup'].add_command(label="Insert Step", command=lambda: self.insert_timeline_step(item_number))
        self.gui['popup'].add_command(label="Delete Step", command=lambda: self.delete_timeline_step(item_number))
        self.gui['popup'].post(event.x_root, event.y_root)

    def insert_timeline_step(self, ind):
        self.gui['tFrame'].add_step_callback(self.controller, ind)
        self.draw_timeline_steps()
        self.backup_timeline()

    def delete_timeline_step(self, ind):
        del self.controller.timelineSteps[ind]
        self.draw_timeline_steps()
        self.backup_timeline()

    def on_timeline_table_select(self, event):
        pass

    def draw_timeline_steps(self):
        tree = self.gui['timelineTree']
        timeline_steps = self.controller.timelineSteps
        # clear table first
        for i in tree.get_children():
            tree.delete(i)
        # add values to table
        ii = 1
        for stepDist in timeline_steps:
            step_name = stepDist['SN']
            period = stepDist['P']
            duration = stepDist['D']
            imaging_or_uncaging = stepDist['IU']
            exclusive = stepDist['EX']
            tree.insert("", ii, text=str(ii), values=(step_name, imaging_or_uncaging, exclusive, period, duration))
            ii += 1

        self.create_timeline_chart()

    def backup_timeline(self):
        timeline_steps = self.controller.timelineSteps
        pickle.dump(timeline_steps, open(self.controller.get_app_param('initDirectory') + 'timelineSteps.p', 'wb'))


class TimelineStepsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller

        # StringVars
        stagger_setting = self.controller.get_settings('stagger')
        if stagger_setting is None:
            stagger_setting = 5
        self.staggerEntryVar = tk.StringVar(self)
        self.staggerEntryVar.set(stagger_setting)
        self.staggerEntryVar.trace('w', parent.create_timeline_chart)
        self.image_uncage = tk.StringVar(self)
        self.image_uncage.set("Image")
        self.image_uncage.trace('w', self.image_in_from_frame)
        self.exclusiveVar = tk.BooleanVar(self)

        # Gui Elements
        self.gui = dict()
        self.gui['label1'] = ttk.Label(self, text='Step Name:', font=self.controller.get_app_param('large_font'))
        self.gui['label1'].grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        self.stepName = tk.StringVar(self)
        self.gui['step_name_entry'] = ttk.Entry(self, width=30, textvariable=self.stepName)
        self.gui['step_name_entry'].grid(row=0, column=1, sticky='nw', padx=10, pady=10)

        self.gui['place_holder_frame'] = ttk.Frame(self)
        self.gui['place_holder_frame'].grid(row=1, column=1, columnspan=1, sticky='nw', pady=10)
        self.gui['place_holder_frame'] = ttk.Frame(self.gui['place_holder_frame'])
        self.gui['place_holder_frame'].pack(side='left', anchor='w')
        self.gui['radio_button1'] = ttk.Radiobutton(self, text='Image', variable=self.image_uncage,
                                                    value='Image')
        self.gui['radio_button1'].grid(row=1, column=0, sticky='nw', pady=10, padx=10)
        self.gui['period_label1'] = ttk.Label(self.gui['place_holder_frame'], text='  Period: ',
                                              font=self.controller.get_app_param('large_font'))
        self.gui['period_label1'].pack(anchor='w', side='left')
        self.periodEntryVar = tk.StringVar(self)
        self.gui['period_entrybel1'] = ttk.Entry(self.gui['place_holder_frame'], width=4,
                                                 textvariable=self.periodEntryVar)
        self.gui['period_entrybel1'].pack(anchor='w', side='left')
        self.gui['period_label2'] = ttk.Label(self.gui['place_holder_frame'], text='sec, ',
                                              font=self.controller.get_app_param('large_font'))
        self.gui['period_label2'].pack(anchor='w', side='left')
        self.gui['duration_label1'] = ttk.Label(self.gui['place_holder_frame'], text='Duration: ',
                                                font=self.controller.get_app_param('large_font'))
        self.gui['duration_label1'].pack(anchor='w', side='left')
        self.durationEntryVar = tk.StringVar(self)
        self.gui['duration_entry'] = ttk.Entry(self.gui['place_holder_frame'], width=4,
                                               textvariable=self.durationEntryVar)
        self.gui['duration_entry'].pack(anchor='w', side='left')
        self.gui['duration_label2'] = ttk.Label(self.gui['place_holder_frame'], text='min',
                                                font=self.controller.get_app_param('large_font'))
        self.gui['duration_label2'].pack(anchor='w', side='left')
        self.gui['radio_button2'] = ttk.Radiobutton(self, text='Uncage', variable=self.image_uncage,
                                                    value='Uncage')
        self.gui['radio_button2'].grid(row=2, column=0, sticky='nw', padx=10, pady=3)
        self.gui['exclusive_checkbutton'] = ttk.Checkbutton(self, text='Exclusive', variable=self.exclusiveVar)
        self.gui['exclusive_checkbutton'].grid(row=2, column=1, sticky='nw', padx=10, pady=3)
        self.gui['stagger_frame'] = ttk.Frame(self)
        self.gui['stagger_frame'].grid(row=4, column=0, sticky='nw', columnspan=2)
        self.gui['stagger_label1'] = ttk.Label(self.gui['stagger_frame'], text='Stagger: ',
                                               font=self.controller.get_app_param('large_font'))
        self.gui['stagger_label1'].grid(row=0, column=0, sticky='nw', padx=10, pady=10)

        self.gui['stagger_entry'] = ttk.Entry(self.gui['stagger_frame'], width=4, textvariable=self.staggerEntryVar)
        self.gui['stagger_entry'].grid(row=0, column=1, sticky='nw', padx=0, pady=10)
        self.gui['stagger_label2'] = ttk.Label(self.gui['stagger_frame'], text='min',
                                               font=self.controller.get_app_param('large_font'))
        self.gui['stagger_label2'].grid(row=0, column=2, sticky='nw', padx=0, pady=10)

        self.gui['add_step_button'] = ttk.Button(self, text="Add Step",
                                                 command=lambda: self.add_step_callback(controller))
        self.gui['add_step_button'].grid(row=3, column=0, padx=10, pady=10, sticky='wn')
        self.gui['place_holder_frame'] = self.gui['place_holder_frame']

    def add_step_callback(self, cont, ind=None):
        # get values
        step_name = self.stepName.get()
        period = floatOrNone(self.periodEntryVar.get())
        duration = floatOrNone(self.durationEntryVar.get())
        imaging_or_uncaging = self.image_uncage.get()
        exclusive = self.exclusiveVar.get()
        cont.add_timeline_step({'SN': step_name,
                                'IU': imaging_or_uncaging,
                                'EX': exclusive,
                                'P': period,
                                'D': duration}, ind)
        # reset values
        self.stepName.set('')
        self.periodEntryVar.set('')
        self.durationEntryVar.set('')
        cont.frames[TimelinePage].backup_timeline()

    def image_in_from_frame(self, *args):
        var = self.image_uncage.get()
        if var == "Image":
            self.gui['place_holder_frame'].pack(side='left', anchor='w')
            self.exclusiveVar.set(False)
        else:
            self.gui['place_holder_frame'].pack_forget()
            self.exclusiveVar.set(True)
