"""
@author: smirnovm
"""
import numpy as np
from matplotlib.figure import Figure
from guis.MacroWindow import MacroWindow
from guis.PositionsPage import PositionsPage
from guis.SettingsPage import SettingsPage
import tkinter as tk
from tkinter import ttk

from guis.SpineRecognitionPage import SpineRecognitionPage
from guis.StartPage import StartPage
from guis.TimelinePage import TimelinePage
from guis.ConnectionsPage import ConnectionsPage

import os  # Ryohei for making crabIco path cleaner.


class MainGuiBuilder(tk.Tk):

    def __init__(self, session):
        tk.Tk.__init__(self)
        crabIcoPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images", "crabIco.ico")  # path to ico
        tk.Tk.iconbitmap(self, default=crabIcoPath)
        tk.Tk.wm_title(self, "SpineTracker")
        tk.Tk.geometry(self, newGeometry='1000x600+200+200')
        self.session = session
        self.settings = None
        self.container = ttk.Notebook(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.protocol("WM_DELETE_WINDOW", self.run_on_exit)
        self.frames = None
        self.windows = None
        self.shared_figs = None

    def build_guis(self):
        self.settings = self.session.settings
        self.shared_figs = self.build_shared_figs()
        self.frames = self.build_frames()

    def run_on_exit(self):
        self.session.exit()

    def build_frames(self):
        frames = {}
        for F in (StartPage, SettingsPage, PositionsPage, TimelinePage, SpineRecognitionPage, ConnectionsPage):
            frame = F(self.container, self.session)
            frames[F] = frame
            self.container.add(frame, text=F.name)
        return frames

    def build_macro_window(self):
        self.windows = {MacroWindow: MacroWindow(self.session)}
        ## TODO: These still need to be extracted from macro window
        ## TODO: and put in a separate file. Basically, all actual functions need to be separated from GUIs better.
        self.windows[MacroWindow].events['run_automated_experiment'] += self.run_automated_experiment
        self.windows[MacroWindow].events['load_macro_image'] += self.load_macro_image
        self.windows[MacroWindow].events['add_position_on_image_click'] += self.add_position_on_image_click
        self.windows[MacroWindow].events['get_large_font'] += self.session.settings.get('large_font')

    def run_automated_experiment(self):
        self.load_macro_image()
        self.define_positions_from_spines()
        self.session.align_all_positions_to_refs()
        self.session.start_imaging()

    def define_positions_from_spines(self):
        XYRBSZ = self.session.state.macro_image.found_spines
        max_pos = self.settings.get('max_positions')
        # spines should already be ordered by score but just in case...
        XYRBSZ = XYRBSZ[np.argsort(XYRBSZ[:, 4][::-1], axis=0), :]
        # TODO: user can select how spines are picked. Either pick top 5, or maybe a random sample from top xx amount
        x_centers_standardized = np.mean(XYRBSZ[:max_pos, [0, 2]], axis=1) / \
                                 self.session.state.macro_image.image_stack.shape[1]
        y_centers_standardized = np.mean(XYRBSZ[:max_pos, [1, 3]], axis=1) / \
                                 self.session.state.macro_image.image_stack.shape[0]
        for x, y, z in zip(x_centers_standardized, y_centers_standardized, XYRBSZ[:max_pos, 5]):
            self.add_position_on_image_click(x, y, z)

    def add_position_on_image_click(self, x, y, z):
        # translate to normal coordinates
        fov_x, fov_y = np.array([self.session.settings.get('fov_x'), self.session.settings.get('fov_y')]) / float(
            self.session.settings.get('macro_zoom'))
        # xy currently originate from top left of image.
        # translate them to coordinate plane directionality.
        # also, make them originate from center
        xyz_center = self.session.state.center_coordinates.get_motor()
        xyz_clicked = {'x': x, 'y': y, 'z': z}
        x = x - .5
        y = -y + .5
        # translate coordinates to µm
        x = x * fov_x + xyz_center['x']
        y = y * fov_y + xyz_center['y']
        z = z + xyz_center['z'] - self.image.n_frames / 2
        # add coordinates to position table
        print('x, y, z = {0}, {1}, {2}'.format(x, y, z))
        self.session.state.current_coordinates.set_scan_voltages_x_y(0, 0)
        self.session.state.current_coordinates.set_motor(x, y, z)
        self.get_ref_images_from_macro(xyz_clicked)
        self.session.create_new_position(take_new_refs=False)

    def get_ref_images_from_macro(self, xyz_clicked):
        image_ref = self.get_ref_image_from_macro(xyz_clicked)
        image_ref_zoomed_out = self.get_zoomed_out_ref_image_from_macro(xyz_clicked)
        self.session.state.ref_image.set_stack(image_ref)
        self.session.state.ref_image_zoomed_out.set_stack(image_ref_zoomed_out)

    def get_ref_image_from_macro(self, xyz_clicked):
        zoom = float(self.session.settings.get('imaging_zoom'))
        slice_count = self.session.settings.get('imaging_slices')
        slice_index = self.get_slice_index(slice_count)
        pixel_index_x_y = self.identify_image_pixel_indices(xyz_clicked, zoom)
        image_ref = self.build_reference_image(slice_index, pixel_index_x_y)
        return image_ref

    def load_macro_image(self):
        self.session.collect_new_macro_image()
        # TODO: Loading this image doesn't always work. Figure out why... Sometimes, it loads the old image.
        # TODO: open this image automatically when macro window is launched
        self.session.communication.get_motor_position()
        xyz = self.session.state.current_coordinates.get_combined(self.session)
        self.session.state.center_coordinates.set_motor(xyz['x'], xyz['y'], xyz['z'])
        self.image = self.session.state.macro_image.pil_image
        self.multi_slice_viewer()

    def build_shared_figs(self):
        fig_dpi = self.settings.get('fig_dpi')
        return SharedFigs(fig_dpi)

    def reset_figure_for_af_images(self, current_image):
        self.frames[StartPage].clear_drift_image_axes()
        self.frames[StartPage].create_drift_image_axes(current_image)

    def show_drift_numbers(self, drift_x_y_z):
        self.settings.set('drift_label',
                          'Drift: {0:.1f}µm in x,'
                          ' {1:.1f}µm in y, and {2:.1} in z'
                          .format(drift_x_y_z.x_um,
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

    def select_current_position_position_page_tree(self, pos_id):
        self.frames[PositionsPage].select_current_position(pos_id)

    def rebuild_timeline(self, *args):
        self.frames[TimelinePage].create_timeline_chart()

    def switch_between_image_and_uncage_guis(self, *args):
        self.frames[TimelinePage].gui['tFrame'].image_uncage_radiobutton_switch()

    def toggle_manual_fov_entering(self, *args):
        self.frames[SettingsPage].toggle_fov_mode()

    def show_end_of_path(self, *args):
        self.frames[SpineRecognitionPage].put_cursor_at_end_of_path()

    def indicate_step_on_timeline(self, step):
        self.frames[TimelinePage].highlight_current_step(step)
        self.frames[StartPage].update_canvases()

    def set_log_path(self):
        self.frames[StartPage].set_log_path()

    def toggle_pipe_connection(self):
        self.session.communication.pipe_connect()

    def print_sent_command(self, line):
        self.frames[ConnectionsPage].show_text('s', line)

    def print_received_command(self, line):
        self.frames[ConnectionsPage].show_text('r', line)


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
