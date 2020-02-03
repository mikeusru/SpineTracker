import os
import tkinter as tk

import numpy as np

from app.Setting import Setting


class SettingsDTO(dict):
    """Data Transfer Object, initializes all the settings"""

    def __init__(self, container):
        super(SettingsDTO, self).__init__()
        self.container = container

        # Settings set here
        self._create_entered_variable('experiment_log_directory', './temp/logs')
        self._create_entered_variable('huge_font', ("Verdana", 18))
        self._create_entered_variable('large_font', ("Verdana", 12))
        self._create_entered_variable('normal_font', ("Verdana", 10))
        self._create_entered_variable('fig_dpi', 100)
        self._create_entered_variable('init_directory', "./iniFiles/")
        self._create_entered_variable('input_file', "./instructions_fromFLIMage.txt")
        self._create_entered_variable('output_file', "./instructions_fromSpineTracker.txt")

        # Settings set in command line
        self._create_command_line_variable('simulation', False)
        self._create_command_line_variable('verbose', False)

        self.initialize_gui_variables()
        self.initialize_acquired_variables()

    def initialize_gui_variables(self):
        self._create_gui_variable('stagger', tk.StringVar, True, 5, dtype=np.int)
        self._create_gui_variable('drift_correction_channel', tk.StringVar, True, 1, dtype=np.int)
        self._create_gui_variable('total_channels', tk.StringVar, True, 2, dtype=np.int)
        self._create_gui_variable('imaging_zoom', tk.StringVar, True, 30, dtype=np.int)
        self._create_gui_variable('imaging_slices', tk.StringVar, True, 3, dtype=np.int)
        self._create_gui_variable('reference_zoom', tk.StringVar, True, 10, dtype=np.int)
        self._create_gui_variable('reference_slices', tk.StringVar, True, 10, dtype=np.int)
        self._create_gui_variable('park_xy_motor', tk.BooleanVar, True, True)
        self._create_gui_variable('macro_resolution_x', tk.StringVar, True, 512, dtype=np.int)
        self._create_gui_variable('macro_resolution_y', tk.StringVar, True, 512, dtype=np.int)
        self._create_gui_variable('max_positions', tk.StringVar, True, 0, dtype=np.int)
        self._create_gui_variable('normal_resolution_x', tk.StringVar, True, 128, dtype=np.int)
        self._create_gui_variable('normal_resolution_y', tk.StringVar, True, 128, dtype=np.int)
        self._create_gui_variable('macro_zoom', tk.StringVar, True, 1, dtype=np.int)
        self._create_gui_variable('macro_z_slices', tk.StringVar, True, 10, dtype=np.int)
        self._create_gui_variable('uncaging_roi_toggle', tk.BooleanVar, True, False)
        self._create_gui_variable('manual_fov_toggle', tk.BooleanVar, True, True)
        self._create_gui_variable('fov_x', tk.StringVar, True, 250, dtype=np.int)
        self._create_gui_variable('fov_y', tk.StringVar, True, 250, dtype=np.int)
        self._create_gui_variable('image_or_uncage', tk.StringVar, False, 'Image')
        self._create_gui_variable('exclusive', tk.BooleanVar, False, False)
        self._create_gui_variable('invert_scan_shift_x', tk.BooleanVar, True, False)
        self._create_gui_variable('invert_scan_shift_y', tk.BooleanVar, True, False)
        self._create_gui_variable('invert_motor_x', tk.BooleanVar, True, False)
        self._create_gui_variable('invert_motor_y', tk.BooleanVar, True, False)
        self._create_gui_variable('invert_drift_x', tk.BooleanVar, True, False)
        self._create_gui_variable('invert_drift_y', tk.BooleanVar, True, False)
        self._create_gui_variable('invert_x_position_canvas_axis', tk.BooleanVar, True, False)
        self._create_gui_variable('invert_y_position_canvas_axis', tk.BooleanVar, True, False)
        self._create_gui_variable('af_box_size_um', tk.StringVar, True, 4.0, dtype=np.float32)
        self._create_gui_variable('uncaging_while_imaging', tk.BooleanVar, False, False)
        self._create_gui_variable('iterations', tk.StringVar, False, 5, dtype=np.int)
        self._create_gui_variable('period', tk.StringVar, False, 60, dtype=np.int)
        self._create_gui_variable('pipe_connect_bool', tk.BooleanVar, False, False)
        self._create_gui_variable('step_name', tk.StringVar, False, "StepName")
        self._create_gui_variable('custom_command', tk.StringVar, False, "")
        self._create_gui_variable('imaging_settings_file', tk.StringVar, False, "")
        self._create_gui_variable('communication_log', tk.StringVar, False, 'Communication Log...')
        self._create_gui_variable('drift_label', tk.StringVar, False, 'Drift: ')
        self._create_gui_variable('display_timer', tk.StringVar, True, '0 s')

    def initialize_acquired_variables(self):
        self._create_acquired_variable('fov_x_y', np.array([250, 250]), dtype=np.float32)
        self._create_acquired_variable('scan_voltage_multiplier', np.array([1, 1]), dtype=np.float32)
        self._create_acquired_variable('scan_voltage_range_reference', np.array([15, 15]), dtype=np.float32)
        self._create_acquired_variable('rotation', 0, dtype=np.float32)
        self._create_acquired_variable('zstep', 1, dtype=np.float32)
        self._create_acquired_variable('macro_image', np.zeros([128, 128]), dtype=np.uint8)
        self._create_acquired_variable('image_file_path', '../test/test_image.tif', dtype=str)
        self._create_acquired_variable('current_zoom', 1, dtype=np.float32)
        self._create_acquired_variable('z_slice_num', np.array([0]), dtype=np.int)
        self._create_acquired_variable('resolution_x_y', np.array([0]), dtype=np.int)
        self._create_acquired_variable('intensity_saving', np.array([0]), dtype=np.int)

    def _create_entered_variable(self, name, default):
        self._create_variable(name, gui_var=None, saved=False, default=default, callback=None, dtype=None)

    def _create_command_line_variable(self, name, default):
        self._create_variable(name, gui_var=None, saved=False, default=default, callback=None, dtype=None)

    def _create_acquired_variable(self, name, default, dtype=None):
        self._create_variable(name, gui_var=None, saved=False, default=default, callback=None, dtype=dtype)

    def _create_gui_variable(self, name, gui_var, saved, default, callback=None, dtype=None):
        gui_var = gui_var(master=self.container, name=name)
        self._create_variable(name, gui_var, saved, default, callback, dtype)

    def _create_variable(self, name,
                         gui_var=None,
                         saved=False,
                         default=None,
                         callback=None,
                         dtype=None):
        self[name] = Setting(name, gui_var, saved, default, callback, dtype)