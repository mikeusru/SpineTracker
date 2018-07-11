import tkinter as tk
from tkinter import ttk

import matplotlib
from matplotlib import patches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from app.Timeline import TimelineStepBlock
from utilities.helper_functions import fit_fig_to_canvas

matplotlib.use("TkAgg")


class TimelinePage(ttk.Frame):
    name = 'Timeline'

    def __init__(self, container, session):
        ttk.Frame.__init__(self, container)
        self.session = session
        self.bind("<Visibility>", self.on_visibility)
        self.selected_item_number = None
        self.color_chart = ColorChart()
        self.gui = self.define_gui_elements()
        self.create_timeline_table()
        self.draw_timeline_steps_general()

    def define_gui_elements(self):
        gui = dict()
        gui['tFrame'] = TimelineStepsFrame(self, self.session)
        gui['tFrame'].grid(row=0, column=0, columnspan=1)
        gui['timeline_figure'] = self.session.gui.shared_figs['timeline_figure']
        gui['timeline_axis'] = self.session.gui.shared_figs['timeline_axis']
        gui['canvas_timeline'] = FigureCanvasTkAgg(gui['timeline_figure'], self)
        gui['canvas_timeline'].get_tk_widget().config(borderwidth=1,
                                                      background='gray',
                                                      highlightcolor='gray',
                                                      highlightbackground='gray')
        gui['canvas_timeline'].draw()
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
        # tree.bind("<<TreeviewSelect>>", self.on_timeline_table_select)
        tree.grid(row=0, column=0, sticky='nsew')
        scroll = ttk.Scrollbar(tree.master, orient="vertical", command=tree.yview)
        scroll.grid(row=0, column=1, sticky='nse', pady=10)
        tree.configure(yscrollcommand=scroll.set)

    def on_visibility(self, event):
        fit_fig_to_canvas(self.gui['timeline_figure'], self.gui['canvas_timeline'],
                          self.session.settings.get('fig_dpi'))
        self.redraw_canvas()
        self.create_timeline_chart()

    def redraw_canvas(self):
        self.gui['canvas_timeline'].draw_idle()

    def create_timeline_chart(self, *args):
        self.session.timeline.build_full_timeline()
        self.display_timeline_chart()

    # TODO: eventually make the chart its own class
    def display_timeline_chart(self):
        timeline = self.session.timeline
        color_chart = self.color_chart
        self.gui['timeline_axis'].clear()
        y_ind = 0
        for pos_id in timeline.ordered_timelines_by_positions:
            y_range = (y_ind - .4, 0.8)
            x_range_list = []
            color_list = []
            y_ind += 1
            for step in timeline.ordered_timelines_by_positions[pos_id].timeline_step_individual_list:
                x_range_list.append((step['start_time'], step['end_time'] - step['start_time']))
                if not step['exclusive']:
                    color_list.append(color_chart.imaging)
                elif step['exclusive'] and step['imaging_or_uncaging'] == 'Image':
                    color_list.append(color_chart.exclusive_imaging)
                else:
                    color_list.append(color_chart.uncaging)
            self.gui['timeline_axis'].broken_barh(x_range_list, y_range, color=color_list, edgecolor='black')
        self.gui['timeline_axis'].set_yticks(list(range(timeline.get_total_pos_num())))
        self.gui['timeline_axis'].set_yticklabels(timeline.get_y_label_list())
        self.gui['timeline_axis'].axis('tight')
        self.gui['timeline_axis'].set_ylim(auto=True)
        self.gui['timeline_axis'].grid(color='k', linestyle=':')
        y1, y2 = self.gui['timeline_axis'].get_ylim()
        if y2 > y1:
            self.gui['timeline_axis'].invert_yaxis()
        legend_patch_uncaging = patches.Patch(color=color_chart.uncaging, label='Uncaging')
        legend_patch_imaging = patches.Patch(color=color_chart.imaging, label='Imaging')
        legend_patch_exclusive_imaging = patches.Patch(color=color_chart.exclusive_imaging, label='Exclusive Imaging')
        self.gui['timeline_axis'].legend(
            handles=[legend_patch_uncaging, legend_patch_imaging, legend_patch_exclusive_imaging])
        self.redraw_canvas()

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
        if len(tree.selection()) == 0:
            return
        self.selected_item_number = item_number
        self.gui['popup'].post(event.x_root, event.y_root)

    def insert_timeline_step(self, ind):
        self.gui['tFrame'].add_step_callback(self.session, ind)
        self.draw_timeline_steps_general()
        self.session.timeline.backup_timeline()

    def delete_timeline_step(self, ind):
        del self.session.timeline.timeline_steps[ind]
        self.draw_timeline_steps_general()
        self.session.timeline.backup_timeline()

    def draw_timeline_steps_general(self):
        tree = self.gui['timelineTree']
        timeline_steps_general = self.session.timeline.timeline_steps
        # clear table first
        for i in tree.get_children():
            tree.delete(i)
        # add values to table
        ii = 1
        for stepDist in timeline_steps_general:
            step_name = stepDist['step_name']
            period = stepDist['period']
            duration = stepDist['duration']
            imaging_or_uncaging = stepDist['imaging_or_uncaging']
            exclusive = stepDist['exclusive']
            tree.insert("", ii, text=str(ii), values=(step_name, imaging_or_uncaging, exclusive, period, duration))
            ii += 1

        self.create_timeline_chart()


class TimelineStepsFrame(ttk.Frame):
    def __init__(self, container, session):
        ttk.Frame.__init__(self, container)
        self.session = session
        self.container = container
        # Gui Elements
        self.gui = self.define_gui_elements()

    def define_gui_elements(self):
        gui = dict()
        settings = self.session.settings
        gui['label1'] = ttk.Label(self, text='Step Name:', font=self.session.settings.get('large_font'))
        gui['label1'].grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        gui['step_name_entry'] = ttk.Entry(self, width=30,
                                           textvariable=settings.get_gui_var('step_name'))
        gui['step_name_entry'].grid(row=0, column=1, sticky='nw', padx=10, pady=10)
        gui['place_holder_frame'] = ttk.Frame(self)
        gui['place_holder_frame'].grid(row=1, column=1, columnspan=1, sticky='nw', pady=10)
        gui['place_holder_frame'] = ttk.Frame(gui['place_holder_frame'])
        gui['place_holder_frame'].pack(side='left', anchor='w')
        gui['image_radio_button'] = ttk.Radiobutton(self, text='Image',
                                                    variable=settings.get_gui_var('image_or_uncage'),
                                                    value='Image')
        gui['image_radio_button'].grid(row=1, column=0, sticky='nw', pady=10, padx=10)
        gui['period_label1'] = ttk.Label(gui['place_holder_frame'], text='  Period: ',
                                         font=self.session.settings.get('large_font'))
        gui['period_label1'].pack(anchor='w', side='left')
        gui['period_entry'] = ttk.Entry(gui['place_holder_frame'], width=4,
                                        textvariable=settings.get_gui_var('period'))
        gui['period_entry'].pack(anchor='w', side='left')
        gui['period_label2'] = ttk.Label(gui['place_holder_frame'], text='sec, ',
                                         font=self.session.settings.get('large_font'))
        gui['period_label2'].pack(anchor='w', side='left')
        gui['duration_label1'] = ttk.Label(gui['place_holder_frame'], text='Duration: ',
                                           font=self.session.settings.get('large_font'))
        gui['duration_label1'].pack(anchor='w', side='left')
        gui['duration_entry'] = ttk.Entry(gui['place_holder_frame'], width=4,
                                          textvariable=settings.get_gui_var('duration'))
        gui['duration_entry'].pack(anchor='w', side='left')
        gui['duration_label2'] = ttk.Label(gui['place_holder_frame'], text='min',
                                           font=self.session.settings.get('large_font'))
        gui['duration_label2'].pack(anchor='w', side='left')
        gui['uncage_radio_button'] = ttk.Radiobutton(self, text='Uncage',
                                                     variable=settings.get_gui_var('image_or_uncage'),
                                                     value='Uncage')
        gui['uncage_radio_button'].grid(row=2, column=0, sticky='nw', padx=10, pady=3)
        gui['exclusive_checkbutton'] = ttk.Checkbutton(self, text='Exclusive',
                                                       variable=settings.get_gui_var('exclusive'))
        gui['exclusive_checkbutton'].grid(row=2, column=1, sticky='nw', padx=10, pady=3)
        gui['stagger_frame'] = ttk.Frame(self)
        gui['stagger_frame'].grid(row=4, column=0, sticky='nw', columnspan=2)
        gui['stagger_label1'] = ttk.Label(gui['stagger_frame'], text='Stagger: ',
                                          font=self.session.settings.get('large_font'))
        gui['stagger_label1'].grid(row=0, column=0, sticky='nw', padx=10, pady=10)

        gui['stagger_entry'] = ttk.Entry(gui['stagger_frame'], width=4,
                                         textvariable=settings.get_gui_var('stagger'))
        gui['stagger_entry'].grid(row=0, column=1, sticky='nw', padx=0, pady=10)
        gui['stagger_label2'] = ttk.Label(gui['stagger_frame'], text='min',
                                          font=self.session.settings.get('large_font'))
        gui['stagger_label2'].grid(row=0, column=2, sticky='nw', padx=0, pady=10)

        gui['add_step_button'] = ttk.Button(self, text="Add Step", command=self.add_step_callback)
        gui['add_step_button'].grid(row=3, column=0, padx=10, pady=10, sticky='wn')
        gui['place_holder_frame'] = gui['place_holder_frame']
        return gui

    def add_step_callback(self, ind=None, *args):
        # get values
        settings = self.session.settings
        step_name = settings.get('step_name')
        period = settings.get('period')
        duration = settings.get('duration')
        imaging_or_uncaging = settings.get('image_or_uncage')
        exclusive = settings.get('exclusive')
        timeline_step = TimelineStepBlock(step_name=step_name, imaging_or_uncaging=imaging_or_uncaging,
                                          exclusive=exclusive, period=period, duration=duration, index=ind)
        if not timeline_step.is_valid():
            print('Warning - Period and Duration must both be >0 for Imaging Steps')
            return
        self.session.timeline.add_timeline_step(timeline_step)
        self.container.draw_timeline_steps_general()
        # reset values
        settings.set('step_name', '')
        settings.set('period', '')
        settings.set('duration', '')
        self.session.timeline.backup_timeline()

    def image_in_from_frame(self):
        var = self.session.settings.get('image_or_uncage')
        if var == "Image":
            self.gui['place_holder_frame'].pack(side='left', anchor='w')
            self.session.settings.set('exclusive', False)
        else:
            self.gui['place_holder_frame'].pack_forget()
            self.session.settings.set('exclusive', True)


class ColorChart:
    def __init__(self):
        super(ColorChart, self).__init__()
        self.uncaging = 'red'
        self.imaging = 'blue'
        self.exclusive_imaging = 'green'
