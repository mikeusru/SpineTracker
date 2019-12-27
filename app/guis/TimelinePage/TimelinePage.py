import os
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename

from matplotlib import patches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from app.guis.TimelinePage.ColorChart import ColorChart
from app.guis.TimelinePage.TimelineStepsFrame import TimelineStepsFrame
from app.io_communication.Event import initialize_events
from app.utilities.helper_functions import fit_fig_to_canvas


class TimelinePage(ttk.Frame):
    name = 'Timeline'

    def __init__(self, container, session):
        ttk.Frame.__init__(self, container)
        self.bind("<Visibility>", self.on_visibility)
        self.selected_item_number = None
        self.color_chart = ColorChart()
        self.gui = None
        self.shared_figs = None
        self.timeline = None
        self.settings = {
            'large_font': None,
            'fig_dpi': 0
        }
        self.gui_vars = {
            'image_or_uncage': None,
            'step_name': None,
            'period': None,
            'iterations': None,
            'exclusive': None,
            'uncaging_while_imaging': None,
            'custom_command': None,
            'imaging_settings_file': None,
            'stagger': None,
        }
        self.get_setting = None
        self.events = initialize_events([
            'set_setting',
        ])

    def build_gui_items(self):
        gui = dict()
        gui['tFrame'] = TimelineStepsFrame(self)
        gui['tFrame'].grid(row=0, column=0, columnspan=1, sticky='nwse')
        gui['timeline_figure'] = self.shared_figs['timeline_figure']
        gui['timeline_axis'] = self.shared_figs['timeline_axis']
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
        gui['timeline_tree'] = ttk.Treeview(gui['timelineTableFrame'])
        gui['popup'] = tk.Menu(self, tearoff=0)
        gui['popup'].add_command(label="Insert Step Above",
                                 command=lambda: self.insert_timeline_step(self.selected_item_number))
        gui['popup'].add_command(label="Delete Step",
                                 command=lambda: self.delete_timeline_step(self.selected_item_number))
        gui['popup'].add_command(label="Save Timeline As...",
                                 command=lambda: self.save_timeline_as())
        gui['popup'].add_command(label="Load Timeline...",
                                 command=lambda: self.select_timeline_to_load())
        gui['popup'].add_command(label="Clear Timeline",
                                 command=lambda: self.clear_timeline())
        self.gui = gui
        self.create_timeline_table()
        self.draw_timeline_steps_general()

    def create_timeline_table(self):
        tree = self.gui['timeline_tree']
        tree["columns"] = ("sn", "iu", 'ex', "p", "i", "sf", "cc")
        tree.column("#0", width=30)
        tree.column("sn", width=120)
        tree.column("iu", width=60)
        tree.column("ex", width=60)
        tree.column("p", width=60)
        tree.column("i", width=75)
        tree.column("sf", width=75)
        tree.column("cc", width=60)
        tree.heading("#0", text='#')
        tree.heading("sn", text="Step")
        tree.heading("iu", text="Type")
        tree.heading("ex", text="Exclusive")
        tree.heading("p", text="Period (s)")
        tree.heading("i", text="Iterations")
        tree.heading("sf", text="Settings")
        tree.heading("cc", text="Comm")
        tree.bind("<Button-3>", self.on_timeline_table_right_click)
        tree.bind("<Button-1>", self.on_timeline_table_left_click)
        tree.grid(row=0, column=0, sticky='nsew')
        scroll = ttk.Scrollbar(tree.master, orient="vertical", command=tree.yview)
        scroll.grid(row=0, column=1, sticky='nse', pady=10)
        tree.configure(yscrollcommand=scroll.set)

    def on_visibility(self, event):
        fit_fig_to_canvas(self.gui['timeline_figure'], self.gui['canvas_timeline'],
                          self.settings['fig_dpi'])
        self.redraw_canvas()
        self.create_timeline_chart()

    def redraw_canvas(self):
        self.gui['canvas_timeline'].draw_idle()

    def create_timeline_chart(self, *args):
        self.timeline.build_full_timeline()
        self.display_timeline_chart()

    # TODO: eventually make the chart its own class
    def display_timeline_chart(self):
        timeline = self.timeline
        color_chart = self.color_chart
        self.gui['timeline_axis'].clear()
        y_ind = 0
        for pos_id in timeline.ordered_timelines_by_positions:
            y_range = (y_ind - .4, 0.8)
            x_range_list = []
            color_list = []
            y_ind += 1
            for step in timeline.ordered_timelines_by_positions[pos_id].timeline_step_individual_list:
                x_range_list.append((step['start_time'] / 60, step['end_time'] / 60 - step['start_time'] / 60))
                if not step['exclusive']:
                    color_list.append(color_chart.imaging)
                elif step['exclusive'] and step['image_or_uncage'] == 'Image' and not step['uncaging_while_imaging']:
                    color_list.append(color_chart.exclusive_imaging)
                elif step['uncaging_while_imaging']:
                    color_list.append(color_chart.uncaging_while_imaging)
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
        legend_patch_uncaging_while_imaging = patches.Patch(color=color_chart.uncaging_while_imaging, label='Imaging + Uncaging')
        self.gui['timeline_axis'].legend(
            handles=[legend_patch_uncaging, legend_patch_imaging, legend_patch_exclusive_imaging, legend_patch_uncaging_while_imaging])
        self.redraw_canvas()

    def on_timeline_table_left_click(self, event):
        tree = self.gui['timeline_tree']
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
        ts = self.timeline.timeline_steps[item_number]
        self.gui['tFrame'].download_from_timeline_step(ts)

    def on_timeline_table_right_click(self, event):
        tree = self.gui['timeline_tree']
        iid = tree.identify_row(event.y)
        item_number = None
        if iid:
            # mouse over item
            tree.selection_set(iid)
        for item in tree.selection():
            item_text = tree.item(item, "text")
            item_number = tree.index(item)
        self.selected_item_number = item_number
        self.gui['popup'].post(event.x_root, event.y_root)

    def insert_timeline_step(self, ind):
        self.gui['tFrame'].add_step_callback(ind)
        self.draw_timeline_steps_general()
        self.timeline.backup_timeline()

    def delete_timeline_step(self, ind):
        if ind is None:
            return
        del self.timeline.timeline_steps[ind]
        self.draw_timeline_steps_general()
        self.timeline.backup_timeline()

    def save_timeline_as(self):
        path = asksaveasfilename(initialfile=os.path.expanduser("") + "timeline_steps.p",
                                 title="Select file",
                                 filetypes=(("pickle file", ".p"),),
                                 defaultextension='.p')
        self.timeline.backup_timeline(path)

    def clear_timeline(self):
        while len(self.timeline.timeline_steps) > 0:
            del self.timeline.timeline_steps[0]
        self.draw_timeline_steps_general()

    def select_timeline_to_load(self):
        path = askopenfilename(initialdir=os.path.expanduser(""),
                               title="Select file",
                               filetypes=(("pickle file", "*.p"),))
        self.timeline.reload_timeline(path)
        self.draw_timeline_steps_general()

    def draw_timeline_steps_general(self):
        tree = self.gui['timeline_tree']
        timeline_steps_general = self.timeline.timeline_steps
        # clear table first
        for i in tree.get_children():
            tree.delete(i)
        # add values to table
        ii = 1
        for stepDist in timeline_steps_general:
            step_name = stepDist['step_name']
            period = stepDist['period']
            iterations = stepDist['iterations']
            image_or_uncage = stepDist['image_or_uncage']
            exclusive = stepDist['exclusive']
            custom_command = stepDist['custom_command']
            imaging_settings_file = os.path.basename(stepDist['imaging_settings_file'])
            tree.insert("", ii, text=str(ii),
                        values=(step_name, image_or_uncage, exclusive, period, iterations, imaging_settings_file, custom_command))
            ii += 1

        self.create_timeline_chart()

    def highlight_current_step(self, step):
        self.display_timeline_chart()
        timeline = self.timeline
        current_pos_id = step.get('pos_id')
        start_time = step.get('start_time') / 60
        end_time = step.get('end_time') / 60
        x_range = (start_time, end_time - start_time)  # x_min, x_width.
        y_ind = 0
        for pos_id in timeline.ordered_timelines_by_positions:
            if pos_id == current_pos_id:
                y_range = (y_ind - .4, 0.8)
                self.gui['timeline_axis'].broken_barh([x_range],
                                                      y_range,
                                                      facecolor=None,
                                                      edgecolor=self.color_chart.selected_edge,
                                                      linewidth=2)
            y_ind += 1


