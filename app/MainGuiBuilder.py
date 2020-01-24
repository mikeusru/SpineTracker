"""
@author: smirnovm
"""
from app.guis.MacroWindow import MacroWindow
from app.guis.PositionsPage import PositionsPage
from app.guis.SettingsPage import SettingsPage
import tkinter as tk
from tkinter import ttk

from app.guis.SharedFigs import SharedFigs
from app.guis.StartPage import StartPage
from app.guis.TimelinePage.TimelinePage import TimelinePage
from app.guis.ConnectionsPage import ConnectionsPage

import os


class MainGuiBuilder(tk.Tk):

    def __init__(self, session):
        tk.Tk.__init__(self)
        icon_path = os.path.join("images", "crabIco.ico")  # path to ico
        tk.Tk.iconbitmap(self, default=icon_path)
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
        self.frames = self.initialize_frames()

    def build_frame(self, frame):
        self.settings.assign_settings(frame.settings)
        self.settings.assign_gui_vars(frame.gui_vars)

        if frame.name == 'Main':
            frame.shared_figs = self.shared_figs
            frame.events['start_imaging'] += self.session.start_imaging
            frame.events['stop_imaging'] += self.session.stop_imaging

        elif frame.name == 'Settings':
            frame.events['save_settings'] += self.session.settings.save_settings
            frame.events['load_settings'] += self.session.settings.load_settings

        elif frame.name == 'Positions':
            frame.shared_figs = self.shared_figs
            frame.events['move_to_pos_id'] += self.session.move_to_pos_id
            frame.events['align_position_to_ref'] += self.session.align_position_to_ref
            frame.events['update_position'] += self.session.update_position
            frame.events['update_reference_images'] += self.session.update_reference_images
            frame.events['remove_position'] += self.session.remove_position
            frame.events['create_new_position'] += self.session.create_new_position
            frame.events['clear_positions'] += self.session.clear_positions
            frame.events['build_macro_window'] += self.build_macro_window
            frame.events['align_all_positions_to_refs'] += self.session.align_all_positions_to_refs
            frame.events['image_all_positions'] += self.session.image_all_positions
            frame.positions = self.session.positions

        elif frame.name == 'Timeline':
            frame.shared_figs = self.shared_figs
            frame.timeline = self.session.timeline
            frame.get_setting = self.session.settings.get
            frame.events['set_setting'] += self.session.settings.set

        elif frame.name == 'Connections':
            ''

        frame.build_gui_items()

    def run_on_exit(self):
        self.session.exit()

    def initialize_frames(self):
        frames = {}
        for F in (StartPage, SettingsPage, PositionsPage, TimelinePage, ConnectionsPage):
            frame = F(self.container, self.session)
            frames[F] = frame
            self.build_frame(frame)
            self.container.add(frame, text=F.name)
        return frames

    def build_macro_window(self):
        self.windows = {MacroWindow: MacroWindow(self.session)}

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

    def toggle_uncaging_while_imaging(self, *args):
        self.frames[TimelinePage].gui['tFrame'].uncaging_while_imaging_checkbutton_on()

    def toggle_manual_fov_entering(self, *args):
        self.frames[SettingsPage].toggle_fov_mode()

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
