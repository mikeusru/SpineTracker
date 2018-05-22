import tkinter as tk
from tkinter import ttk
import matplotlib
import numpy as np

from flow.TimelineStep import TimelineStep, MiniTimelineStep
from utilities.helper_functions import fit_fig_to_canvas
from utilities.math_helpers import float_or_zero, float_or_none
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
        self.selected_item_number = None

        # Define GUI elements
        self.gui = self.define_gui_elements()

        self.create_timeline_table()
        self.draw_timeline_steps()

    def define_gui_elements(self):
        gui = dict()
        gui['tFrame'] = TimelineStepsFrame(self, self.controller)
        gui['tFrame'].grid(row=0, column=0, columnspan=1)
        gui['timeline_figure'] = self.controller.shared_figs['timeline_figure']
        gui['timeline_axis'] = self.controller.shared_figs['timeline_axis']
        gui['canvas_timeline'] = FigureCanvasTkAgg(gui['timeline_figure'], self)
        gui['canvas_timeline'].get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                                      highlightbackground='gray')
        gui['canvas_timeline'].show()
        gui['canvas_timeline'].get_tk_widget().grid(row=2, column=0, columnspan=2,
                                                    padx=10, pady=10, sticky='nsew')
        gui['timelineTableFrame'] = ttk.Frame(self)
        gui['timelineTableFrame'].grid(row=0, column=1, padx=10, pady=10)
        gui['timelineTree'] = ttk.Treeview(gui['timelineTableFrame'])
        gui['popup'] = tk.Menu(self, tearoff=0)
        gui['popup'].add_command(label="Insert Step",
                                 command=lambda: self.insert_timeline_step(self.selected_item_number))
        gui['popup'].add_command(label="Delete Step",
                                 command=lambda: self.delete_timeline_step(self.selected_item_number))
        return gui

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
        fit_fig_to_canvas(self.gui['timeline_figure'], self.gui['canvas_timeline'],
                          self.controller.get_app_param('fig_dpi'))
        self.gui['canvas_timeline'].draw_idle()
        self.create_timeline_chart()

    def create_timeline_chart(self, *args):
        """Creates chart of timeline from scratch"""
        class IndividualPositionTimeline:
            def __init__(self, pos_id, pos_count, stagger):
                self.stagger = stagger
                self.pos_id = pos_id
                self.y_label = 'Position {}'.format(pos_id)
                self.total_time = 0
                self.pos_count = pos_count
                self.start_end_time_array = []
                self.current_index = 0
                self.mini_steps = []
                self.min_start_time = 0
                # TODO: I bet it would be easier if each individual step was its own instance... another refactoring of the TimelineStep class

            def add_step(self, step):
                start_time = self.total_time
                if start_time == 0:
                    duration = step['duration'] + self.stagger * self.pos_count
                else:
                    duration = step['duration']
                period = step['period']
                # TODO: This is done so the exclusively imaged zone shifts as one thing, but may cause a bug later. fix this.
                if step['exclusive']:
                    period = duration * 60
                start_end_time_single_step = self.calc_start_end_time(period, duration, start_time)
                self.start_end_time_array.append(start_end_time_single_step)
                self.total_time += duration

            def calc_start_end_time(self, period, duration, start_time):
                start_times_single_step = self.calc_start_times(period, duration, start_time)
                end_times_single_step = self.calc_end_times(start_times_single_step,period)
                start_end_single_step = np.array([start_times_single_step, end_times_single_step])
                return start_end_single_step

            def calc_start_times(self, period, duration, start_time):
                start_time_array = np.arange(start_time, start_time + duration, period / 60)
                return start_time_array

            def calc_end_times(self, start_times, period):
                end_times = start_times + period / 60
                return end_times

            def get_next_start_end_time(self):
                # TODO: Instead of dealing with multidimensional numpy arrays, program the shifts into methods
                start_end = self.start_end_time_array[0][0][:, 0]
                start = max(start_end[0], self.min_start_time)
                # add small amount of time based on position so they are added to the queue sequentially, not at the same time
                start = start + (self.pos_count * 0.001)
                end = start + start_end[1] - start_end[0]
                return start, end

            def delete_first_start_end_time(self):
                self.start_end_time_array[0] = np.array(
                    [np.delete(self.start_end_time_array[0][0], 0, 1)])

            def update_min_start_time(self, start_time, end_time, exclusive, reference_pos_id):
                if exclusive:
                    self.min_start_time = np.max(end_time, self.min_start_time)
                else:
                    if self.pos_id == reference_pos_id:
                        self.min_start_time = np.max(self.min_start_time, end_time)
                    self.min_start_time = np.max(self.min_start_time, start_time)

            def is_empty(self):
                if len(self.start_end_time_array) == 0:
                    return True
                else:
                    return False

        class TimelineChart:
            def __init__(self, controller):
                self.controller = controller
                self.timeline_steps = self.controller.timeline_steps
                self.positions = self.define_positions()
                self.stagger = float_or_zero(self.controller.get_settings('stagger'))
                self.pos_id_list = self.positions.keys()
                self.individual_position_timelines = {}

            def is_defined_steps(self):
                if len(self.timeline_steps) == 0:
                    return False
                else:
                    return True

            def define_positions(self):
                positions = self.controller.positions
                if len(positions) == 0:
                    positions = {1: [], 2: [], 3: [], 4: [], 5: []}
                return positions

            def construct_base_timelines(self):
                pos_counter = 0
                for pos_id in self.pos_id_list:
                    self.individual_position_timelines[pos_id] = IndividualPositionTimeline(
                                                            pos_id, pos_counter, self.stagger)
                    for step in self.timeline_steps:
                        self.individual_position_timelines[pos_id].add_step(step)
                    pos_counter += 1

            def get_next_starting_position(self):
                earliest_start_time = np.array(np.inf)
                for pos_id in self.individual_position_timelines:
                    if self.individual_position_timelines[pos_id].is_empty():
                        continue
                    potential_start_time, potential_end_time = self.individual_position_timelines[
                        pos_id].get_next_start_end_time()
                    timeline_step_number = self.individual_position_timelines[pos_id].current_index
                    exclusive = self.timeline_steps[timeline_step_number]['exclusive']
                    if (potential_start_time < earliest_start_time) or (
                            potential_start_time == earliest_start_time and exclusive):
                        earliest_start_time = potential_start_time
                        end_time = potential_end_time
                        first_pos_id = pos_id
                return earliest_start_time, end_time, first_pos_id

            def rebuild_timelines_from_mini_steps(self):
                while True:
                    start_time, end_time, pos_id = self.get_next_starting_position()
                    timeline_step_number = self.individual_position_timelines[pos_id].current_index
                    mini_timeline_step = MiniTimelineStep(self.timeline_steps[timeline_step_number],
                                                           start_time, end_time)
                    self.individual_position_timelines[pos_id].mini_steps.append(mini_timeline_step)
                    self.individual_position_timelines[pos_id].delete_first_start_end_time()
                    self.update_all_min_start_times(start_time,end_time, pos_id)
                    self.move_to_next_step_if_ready(pos_id)
                    if self.is_done_building():
                        break

            def move_to_next_step_if_ready(self, pos_id):
                """If this step is done, move to next step and delete this one"""
                if self.individual_position_timelines[pos_id].start_end_time_array[0].size == 0:
                    self.individual_position_timelines[pos_id].current_index += 1
                    del self.individual_position_timelines[pos_id].start_end_time_array[0]


            def update_all_min_start_times(self, start_time, end_time, pos_id):
                timeline_step_number = self.individual_position_timelines[pos_id].current_index
                exclusive = self.timeline_steps[timeline_step_number]['exclusive']
                pos_count = self.individual_position_timelines[pos_id].pos_count
                for key in self.individual_position_timelines:
                    self.individual_position_timelines[key].update_min_start_time(start_time, end_time, exclusive, pos_id)

            def is_done_building(self):
                """return False if any individual position timelines are not empty yet"""
                for _,individual_position_timeline in self.individual_position_timelines:
                    if not individual_position_timeline.is_empty():
                        return False
                else:
                    return True

            def get_y_label_list(self):
                y_label_list = []
                for _,individual_position_timeline in self.individual_position_timelines:
                    y_label_list.append(individual_position_timeline.y_label)
                return y_label_list

            def get_total_pos_num(self):
                total_pos_num = len(self.pos_id_list)
                return total_pos_num

            def get_mini_steps_by_pos(self):
                mini_steps_by_pos = {}
                for pos_id,individual_position_timeline in self.individual_position_timelines:
                    mini_steps_by_pos[pos_id] = individual_position_timeline.mini_steps
                return mini_steps_by_pos

        self.timeline_chart = TimelineChart(self.controller)
        if not self.timeline_chart.is_defined_steps():
            return
        self.timeline_chart.construct_base_timelines()
        self.timeline_chart.rebuild_timelines_from_mini_steps()
        self.controller.individual_timeline_steps = self.timeline_chart.get_mini_steps_by_pos()
        self.display_timeline_chart()

    def display_timeline_chart(self):
        """Show timeline chart on timeline axis"""
        self.gui['timeline_axis'].clear()
        y_ind = 0
        y_labels = []
        for pos_id in self.timeline_chart.individual_position_timelines:
            y_range = (y_ind - .4, 0.8)
            x_range_list = []
            color_list = []
            y_ind += 1
            for step in self.timeline_chart.individual_position_timelines[pos_id]:
                x_range_list.append((step['start_time'], step['end_time'] - step['start_time']))
                if not step['exclusive']:
                    color_list.append('blue')  # regular imaging
                elif step['exclusive'] and step['imaging_or_uncaging'] == 'Image':
                    color_list.append('green')  # exclusive imaging
                else:
                    color_list.append('red')  # uncaging
            self.gui['timeline_axis'].broken_barh(x_range_list, y_range, color=color_list, edgecolor='black')
        self.gui['timeline_axis'].set_yticks(list(range(self.timeline_chart.get_total_pos_num())))
        self.gui['timeline_axis'].set_yticklabels(self.timeline_chart.get_y_label_list())
        self.gui['timeline_axis'].axis('tight')
        self.gui['timeline_axis'].set_ylim(auto=True)
        self.gui['timeline_axis'].grid(color='k', linestyle=':')
        y1, y2 = self.gui['timeline_axis'].get_ylim()
        if y2 > y1:
            self.gui['timeline_axis'].invert_yaxis()
        legend_patch_red = patches.Patch(color='red', label='Uncaging')
        legend_patch_blue = patches.Patch(color='blue', label='Imaging')
        legend_patch_green = patches.Patch(color='green', label='Exclusive Imaging')
        self.gui['timeline_axis'].legend(handles=[legend_patch_red, legend_patch_blue, legend_patch_green])
        self.gui['canvas_timeline'].draw_idle()

    def on_timeline_table_right_click(self, event):
        tree = self.gui['timelineTree']
        iid = tree.identify_row(event.y)
        item_number = None
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
        self.selected_item_number = item_number
        self.gui['popup'].post(event.x_root, event.y_root)

    def insert_timeline_step(self, ind):
        self.gui['tFrame'].add_step_callback(self.controller, ind)
        self.draw_timeline_steps()
        self.backup_timeline()

    def delete_timeline_step(self, ind):
        del self.controller.timeline_steps[ind]
        self.draw_timeline_steps()
        self.backup_timeline()

    def on_timeline_table_select(self, event):
        # This function is ignored because the class that uses this one as a super also has it
        pass

    def draw_timeline_steps(self):
        tree = self.gui['timelineTree']
        timeline_steps = self.controller.timeline_steps
        # clear table first
        for i in tree.get_children():
            tree.delete(i)
        # add values to table
        ii = 1
        for stepDist in timeline_steps:
            step_name = stepDist['step_name']
            period = stepDist['period']
            duration = stepDist['duration']
            imaging_or_uncaging = stepDist['imaging_or_uncaging']
            exclusive = stepDist['exclusive']
            tree.insert("", ii, text=str(ii), values=(step_name, imaging_or_uncaging, exclusive, period, duration))
            ii += 1

        self.create_timeline_chart()

    def backup_timeline(self):
        timeline_steps = self.controller.timeline_steps
        pickle.dump(timeline_steps, open(self.controller.get_app_param('initDirectory') + 'timeline_steps.p', 'wb'))


class TimelineStepsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller

        # Gui Elements
        self.gui = self.define_gui_elements()

    def define_gui_elements(self):
        gui = dict()
        # TODO: Allow users to add custom steps. The step name is the signal which is sent to the imaging program
        # So like "Custom Step" becomes custom_step and custom_step_done. Ugh this seems hard... hold off for now. This is for version 2.
        gui['label1'] = ttk.Label(self, text='Step Name:', font=self.controller.get_app_param('large_font'))
        gui['label1'].grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        gui['step_name_entry'] = ttk.Entry(self, width=30,
                                           textvariable=self.controller.gui_vars['step_name_string_var'])
        gui['step_name_entry'].grid(row=0, column=1, sticky='nw', padx=10, pady=10)
        gui['place_holder_frame'] = ttk.Frame(self)
        gui['place_holder_frame'].grid(row=1, column=1, columnspan=1, sticky='nw', pady=10)
        gui['place_holder_frame'] = ttk.Frame(gui['place_holder_frame'])
        gui['place_holder_frame'].pack(side='left', anchor='w')
        gui['radio_button1'] = ttk.Radiobutton(self, text='Image',
                                               variable=self.controller.gui_vars['image_or_uncage_string_var'],
                                               value='Image')
        gui['radio_button1'].grid(row=1, column=0, sticky='nw', pady=10, padx=10)
        gui['period_label1'] = ttk.Label(gui['place_holder_frame'], text='  Period: ',
                                         font=self.controller.get_app_param('large_font'))
        gui['period_label1'].pack(anchor='w', side='left')
        gui['period_entry'] = ttk.Entry(gui['place_holder_frame'], width=4,
                                        textvariable=self.controller.gui_vars['period_string_var'])
        gui['period_entry'].pack(anchor='w', side='left')
        gui['period_label2'] = ttk.Label(gui['place_holder_frame'], text='sec, ',
                                         font=self.controller.get_app_param('large_font'))
        gui['period_label2'].pack(anchor='w', side='left')
        gui['duration_label1'] = ttk.Label(gui['place_holder_frame'], text='Duration: ',
                                           font=self.controller.get_app_param('large_font'))
        gui['duration_label1'].pack(anchor='w', side='left')
        gui['duration_entry'] = ttk.Entry(gui['place_holder_frame'], width=4,
                                          textvariable=self.controller.gui_vars['duration_string_var'])
        gui['duration_entry'].pack(anchor='w', side='left')
        gui['duration_label2'] = ttk.Label(gui['place_holder_frame'], text='min',
                                           font=self.controller.get_app_param('large_font'))
        gui['duration_label2'].pack(anchor='w', side='left')
        gui['radio_button2'] = ttk.Radiobutton(self, text='Uncage',
                                               variable=self.controller.gui_vars['image_or_uncage_string_var'],
                                               value='Uncage')
        gui['radio_button2'].grid(row=2, column=0, sticky='nw', padx=10, pady=3)
        gui['exclusive_checkbutton'] = ttk.Checkbutton(self, text='Exclusive',
                                                       variable=self.controller.gui_vars['exclusive_bool_var'])
        gui['exclusive_checkbutton'].grid(row=2, column=1, sticky='nw', padx=10, pady=3)
        gui['stagger_frame'] = ttk.Frame(self)
        gui['stagger_frame'].grid(row=4, column=0, sticky='nw', columnspan=2)
        gui['stagger_label1'] = ttk.Label(gui['stagger_frame'], text='Stagger: ',
                                          font=self.controller.get_app_param('large_font'))
        gui['stagger_label1'].grid(row=0, column=0, sticky='nw', padx=10, pady=10)

        gui['stagger_entry'] = ttk.Entry(gui['stagger_frame'], width=4,
                                         textvariable=self.controller.gui_vars['stagger_string_var'])
        gui['stagger_entry'].grid(row=0, column=1, sticky='nw', padx=0, pady=10)
        gui['stagger_label2'] = ttk.Label(gui['stagger_frame'], text='min',
                                          font=self.controller.get_app_param('large_font'))
        gui['stagger_label2'].grid(row=0, column=2, sticky='nw', padx=0, pady=10)

        gui['add_step_button'] = ttk.Button(self, text="Add Step",
                                            command=lambda: self.add_step_callback(self.controller))
        gui['add_step_button'].grid(row=3, column=0, padx=10, pady=10, sticky='wn')
        gui['place_holder_frame'] = gui['place_holder_frame']
        return gui

    def add_step_callback(self, cont, ind=None):
        # get values
        step_name = self.controller.gui_vars['step_name_string_var'].get()
        period = float_or_none(self.controller.gui_vars['period_string_var'].get())
        duration = float_or_none(self.controller.gui_vars['duration_string_var'].get())
        imaging_or_uncaging = self.controller.gui_vars['image_or_uncage_string_var'].get()
        exclusive = self.controller.gui_vars['exclusive_bool_var'].get()
        timeline_step = TimelineStep(step_name=step_name, imaging_or_uncaging=imaging_or_uncaging,
                                     exclusive=exclusive, period=period, duration=duration, index=ind)
        cont.add_timeline_step(timeline_step)
        # reset values
        self.controller.gui_vars['step_name_string_var'].set('')
        self.controller.gui_vars['period_string_var'].set('')
        self.controller.gui_vars['duration_string_var'].set('')
        cont.frames[TimelinePage].backup_timeline()

    def image_in_from_frame(self, *args):
        var = self.controller.gui_vars['image_or_uncage_string_var'].get()
        if var == "Image":
            self.gui['place_holder_frame'].pack(side='left', anchor='w')
            self.controller.gui_vars['exclusive_bool_var'].set(False)
        else:
            self.gui['place_holder_frame'].pack_forget()
            self.controller.gui_vars['exclusive_bool_var'].set(True)
