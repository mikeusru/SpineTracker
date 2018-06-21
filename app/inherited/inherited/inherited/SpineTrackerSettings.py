import getopt
import os
import pickle
import tkinter as tk
import numpy as np
import sys

from app.inherited.inherited.inherited.inherited.SpineTrackerContainer import SpineTrackerContainer
from utilities.math_helpers import blank_to_none, none_to_blank


class Initializer(SpineTrackerContainer):

    def __init__(self, *args, **kwargs):
        super(Initializer, self).__init__()
        self.settings = SettingsManager(self)
        self.settings.initialize_settings()
        self.command_line_interpreter = CommandLineInterpreter(self.settings, *args)
        self.command_line_interpreter.interpret()


class SettingsManager:

    def __init__(self, container):
        self.container = container
        # self.settings_dto = SettingsDTO(container)
        self.set_default_traces()

    def initialize_settings(self):
        self.settings_dto = SettingsDTO(self.container)

    def set_default_traces(self):
        for name, setting in self.settings_dto.items():
            if setting.needs_default_trace():
                setting.set_trace(self.default_trace)

    def default_trace(self, *args):
        name = args[0]
        self.update_value(name)

    def update_value(self, name):
        self.settings_dto[name].update_value_from_gui()

    def _exists(self, name):
        if name in self.settings_dto.keys():
            return True
        else:
            return False

    def set(self, name, value):
        if self._exists(name):
            self.settings_dto[name].set(value)
        else:
            # TODO: Add error handling here?
            print('Variable {} does not exist. Declare all variables first in SettingsDTO'.format(name))

    def get(self, name):
        return self.settings_dto[name].value

    def get_gui_var(self, name):
        return self.settings_dto[name].gui_var

    def load_settings(self):
        if os.path.isfile(self._get_file_name()):
            settings_dict = pickle.load(open(self._get_file_name(), 'rb'))
            self.update_with_loaded_dict(settings_dict)
            # self.settings_dto.update(settings_dict)

    def update_with_loaded_dict(self, settings_dict):
        for name, setting in settings_dict.items:
            value = setting.value
            self.set(name, value)

    def save_settings(self):
        settings_dict = {}
        for name, setting in self.settings_dto.items():
            if setting.saved:
                settings_dict.update({name: setting})
        pickle.dump(settings_dict, open(self._get_file_name(), 'wb'))

    def _get_file_name(self):
        return self.get('init_directory') + 'user_settings.p'

    def update_gui_from_settings(self, name=None):
        if not name:
            for name, setting in self.settings_dto.items():
                setting.update_gui()
        else:
            self.settings_dto[name].update_gui()


class SettingsDTO(dict):
    """Data Transfer Object, initializes all the settings"""

    def __init__(self, container):
        super(SettingsDTO, self).__init__()
        self.container = container

        # Settings set here
        self._create_entered_variable('experiment_log_file', '../temp/experiment_log.txt')
        self._create_entered_variable('large_font', ("Verdana", 12))
        self._create_entered_variable('fig_dpi', 100)
        self._create_entered_variable('init_directory', "../iniFiles/")
        self._create_entered_variable('input_file', "../instructions_input.txt")
        self._create_entered_variable('output_file', "../instructions_output.txt")

        # Settings set in command line
        self._create_command_line_variable('simulation', False)
        self._create_command_line_variable('verbose', False)

        # Settings set in guis
        self._create_gui_variable('stagger', tk.StringVar, True, 5,
                                  callback=self.container.update_timeline_chart, dtype=np.int)
        self._create_gui_variable('drift_correction_channel', tk.StringVar, True, 1, dtype=np.int)
        self._create_gui_variable('total_channels', tk.StringVar, True, 2, dtype=np.int)
        self._create_gui_variable('imaging_zoom', tk.StringVar, True, 30, dtype=np.int)
        self._create_gui_variable('imaging_slices', tk.StringVar, True, 3, dtype=np.int)
        self._create_gui_variable('reference_zoom', tk.StringVar, True, 10, dtype=np.int)
        self._create_gui_variable('reference_slices', tk.StringVar, True, 10, dtype=np.int)
        self._create_gui_variable('park_xy_motor', tk.BooleanVar, True, True)
        self._create_gui_variable('macro_resolution_x', tk.StringVar, True, 512, dtype=np.int)
        self._create_gui_variable('macro_resolution_y', tk.StringVar, True, 512, dtype=np.int)
        self._create_gui_variable('normal_resolution_x', tk.StringVar, True, 128, dtype=np.int)
        self._create_gui_variable('normal_resolution_y', tk.StringVar, True, 128, dtype=np.int)
        self._create_gui_variable('macro_zoom', tk.StringVar, True, 1, dtype=np.int)
        self._create_gui_variable('macro_z_slices', tk.StringVar, True, 10, dtype=np.int)
        self._create_gui_variable('uncaging_roi_toggle', tk.BooleanVar, True, False)
        self._create_gui_variable('image_or_uncage', tk.StringVar, False, 'Image',
                                  callback=self.container.switch_between_image_and_uncage_guis)
        self._create_gui_variable('exclusive', tk.BooleanVar, False, False)
        self._create_gui_variable('duration', tk.StringVar, False, 5, dtype=np.int)
        self._create_gui_variable('period', tk.StringVar, False, 60, dtype=np.int)
        self._create_gui_variable('step_name', tk.StringVar, False, "StepName")

        # Settings gotten from imaging program
        self._create_acquired_variable('fov_x_y', np.array([250, 250]), dtype=np.float32)
        self._create_acquired_variable('scan_angle_multiplier', np.array([1, 1]), dtype=np.float32)
        self._create_acquired_variable('scan_angle_range_reference', np.array([15, 15]), dtype=np.float32)
        self._create_acquired_variable('current_zoom', None, dtype=np.int)
        self._create_acquired_variable('center_xyz', np.array([0, 0, 0]), dtype=np.float32)
        self._create_acquired_variable('center_coordinates', np.array([0, 0, 0]), dtype=np.float32)
        self._create_acquired_variable('center_scan_angle_x_y', np.array([0, 0]), dtype=np.float32)
        self._create_acquired_variable('macro_image', np.zeros([128, 128]), dtype=np.uint8)
        self._create_acquired_variable('image_file_path', '../test/test_image.tif')
        self._create_acquired_variable('image_stack', np.zeros([128, 128, 3]), dtype=np.uint8)
        self._create_acquired_variable('imgref_ref', np.zeros([128, 128, 3]), dtype=np.uint8)
        self._create_acquired_variable('imgref_imaging', np.zeros([128, 128, 3]), dtype=np.uint8)
        self._create_acquired_variable('shiftxy', np.array([0, 0]), dtype=np.float32)
        self._create_acquired_variable('shiftz', np.array([0]), dtype=np.float32)
        self._create_acquired_variable('shiftxy_pixels', dict(shiftx=0, shifty=0))
        self._create_acquired_variable('focus_list', np.array([0]), dtype=np.float32)
        self._create_acquired_variable('current_zoom', np.array([0]), dtype=np.int)
        self._create_acquired_variable('z_slice_num', np.array([0]), dtype=np.int)
        self._create_acquired_variable('x_y_resolution', np.array([0]), dtype=np.int)

    def _create_entered_variable(self, name, default):
        self._create_variable(name, gui_var=None, saved=False, default=default, callback=None, dtype=None)

    def _create_command_line_variable(self, name, default):
        self._create_variable(name, gui_var=None, saved=False, default=default, callback=None, dtype=None)

    def _create_acquired_variable(self, name, default, dtype=None):
        self._create_variable(name, gui_var=None, saved=False, default=default, callback=None, dtype=dtype)

    def _create_gui_variable(self, name, gui_var, saved, default, callback=None, dtype=None):
        gui_var = gui_var(self.container, name=name)
        self._create_variable(name, gui_var, saved, default, callback, dtype)

    def _create_variable(self, name,
                         gui_var=None,
                         saved=False,
                         default=None,
                         callback=None,
                         dtype=None):
        self[name] = Setting(name, gui_var, saved, default, callback, dtype)


class Setting:

    def __init__(self, name, gui_var, saved, default, callback=None, dtype=None):
        self.setting = name
        self.gui_var = gui_var
        self.saved = saved
        self.default = default
        self.value = None
        self.callback = callback
        self.dtype = dtype

        self.set(self.default)
        self.update_gui()
        self.set_trace()

    def _update_dtype(self):
        if self.dtype is not None:
            self.value = blank_to_none(self.value)
            if self.value is not None:
                self.value = np.array(self.value, dtype=self.dtype)

    def set(self, value):
        self.value = value
        self._update_dtype()
        self.update_gui()

    def update_gui(self):
        if self.gui_var is not None:
            # print('var: {}, value: {}'.format(self.gui_var, self.value))
            value = none_to_blank(self.value)
            self.gui_var.set(value)

    def set_trace(self, callback=None):
        if callback is not None:
            self.callback = callback
        if (self.gui_var is not None) and (self.callback is not None):
            self.gui_var.trace_add('write', self.callback)

    def update_value_from_gui(self):
        self.value = self.gui_var.get()
        self._update_dtype()

    def needs_default_trace(self):
        if (self.gui_var is not None) and (self.callback is None):
            return True
        else:
            return False


class CommandLineInterpreter:

    def __init__(self, settings_manager, *args):
        self.settings_manager = settings_manager
        self.args = args

    def interpret(self):
        args = self.args
        if args is not None:
            args = args[0]
            try:
                options, remainder = getopt.getopt(args, 'sv', ['simulation', 'verbose'])
            except getopt.GetoptError:
                print('Error - incorrect input format')
                print('correct Format: main.py -v -s')
                sys.exit(2)
            for opt, val in options:
                if opt in ('-s', '--simulation'):
                    print('simulation mode on')
                    self._set_setting('simulation', True)
                elif opt in ('-v', '--verbose'):
                    print('verbose mode on')
                    self._set_setting('verbose', True)

    def _set_setting(self, name, value):
        self.settings_manager.set(name, value)
