"""
@author: smirnovm
"""
from matplotlib.figure import Figure

from guis.MacroWindow import MacroWindow
from guis.PositionsPage import PositionsPage
from guis.SettingsPage import SettingsPage
from guis.StartPage import StartPage
from guis.TimelinePage import TimelinePage
import tkinter as tk
from tkinter import ttk


class MainGuiBuilder(tk.Tk):

    def __init__(self, settings):
        self.settings = settings
        tk.Tk.__init__(self)
        tk.Tk.iconbitmap(self, default="../images/crabIco.ico")  # icon doesn't work
        tk.Tk.wm_title(self, "SpineTracker")
        tk.Tk.geometry(self, newGeometry='1000x600+200+200')
        self.container = ttk.Notebook(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.frames = self.build_frames()
        self.windows = self.build_windows()
        self.shared_figs = self.build_shared_figs()
        self.protocol("WM_DELETE_WINDOW", self.run_on_exit)

    def run_on_exit(self):
        print('quitting')
        self.ins_thread.stop()
        print('Instruction listener closed')
        self.log_file.close()
        self.destroy()
        print('goodbye')

    def build_frames(self):
        frames = {}
        for F in (StartPage, SettingsPage, PositionsPage, TimelinePage):
            frame = F(self.container, self)
            frames[F] = frame
            self.container.add(frame, text=F.name)
        return frames

    def build_macro_window(self):
        windows = {MacroWindow: MacroWindow(self)}
        return windows

    def build_shared_figs(self):
        fig_dpi = self.settings.get('fig_dpi')
        return SharedFigs(fig_dpi)

    def reset_figure_for_af_images(self, current_image):
        self.frames[StartPage].clear_drift_image_axes()
        self.frames[StartPage].create_drift_image_axes(current_image)

    def show_drift_numbers(self, drift_x_y_z):
        self.frames[StartPage].gui['drift_label'].configure(
            text='Detected drift of {0:.1f}µm in x, {1:.1f}µm in y, and {2:.1} in z'.format(drift_x_y_z.x_um,
                                                                                            drift_x_y_z.y_um,
                                                                                            drift_x_y_z.z_um))

    def show_drift_info(self, current_image, pos_id=None):
        self.show_drift_numbers(current_image.drift_x_y_z)
        self.show_drift_images(current_image)
        self.update_position_marker(pos_id)
        self.frames[StartPage].update_canvases()

    def show_drift_images(self, current_image):
        self.frames[StartPage].display_image_stack(current_image)
        self.frames[StartPage].indicate_drift_on_images(current_image)

    def update_position_marker(self, pos_id):
        if pos_id is not None:
            self.frames[PositionsPage].select_position_in_graph(pos_id)

    def update_positions_table(self):
        self.frames[PositionsPage].redraw_position_table()


class SharedFigs(dict):

    def __init__(self, fig_dpi, *args, **kwargs):
        super(SharedFigs, self).__init__()

        # Shared Timeline Figure
        self['timeline_figure'] = Figure(figsize=(5, 2), dpi=fig_dpi)
        self['timeline_figure'].set_tight_layout(True)
        self['timeline_axis'] = self['timeline_figure'].add_subplot(111)

        # Shared Positions Figure
        self['f_positions'] = Figure(figsize=(3, 3), dpi=fig_dpi)
        self['f_positions'].subplots_adjust(left=0, right=1, bottom=0, top=1)
        self['f_positions'].set_tight_layout(True)
        self['f_positions'].set_size_inches(4, 4)

# if __name__ == "__main__":
#     app = MainGuiBuilder()
#     app.mainloop()