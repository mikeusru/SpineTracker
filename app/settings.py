import getopt
import os
import pickle
import sys
import tkinter as tk

import numpy as np

from utilities.math_helpers import none_to_blank, blank_to_zero


# TODO: Check if container has to be the giu for creating gui vars, or if it can just be the main app
class SettingsManager:

    def __init__(self, container):
        self.container = container
        self.settings_dto = SettingsDTO(container)
        self.load_settings()

    def initialize_gui_callbacks(self):
        self.set_default_callbacks()

    def set_default_callbacks(self):
        for name, setting in self.settings_dto.items():
            if setting.needs_default_trace():
                setting.set_trace(self.default_callback)

    def default_callback(self, *args):
        name = args[0]
        self.update_value(name)
        if name == 'stagger':
            self.container.update_timeline_chart()
        elif name == 'image_or_uncage':
            self.container.switch_between_image_and_uncage_guis()
        elif name == 'manual_fov_toggle':
            self.container.toggle_manual_fov_entering()
        elif name == 'training_data_path':
            self.container.show_end_of_path()
        elif name == 'trained_model_path':
            self.container.show_end_of_path()
        if self.setting_is_saved(name):
            self.save_settings()

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
        return self.settings_dto[name].get_value()

    def get_gui_var(self, name):
        return self.settings_dto[name].gui_var

    def load_settings(self):
        if os.path.isfile(self._get_file_name()):
            settings_dict = pickle.load(open(self._get_file_name(), 'rb'))
            self.update_with_loaded_dict(settings_dict)

    def update_with_loaded_dict(self, settings_dict):
        for name, value in settings_dict.items():
            self.set(name, value)

    def setting_is_saved(self, name):
        return self.settings_dto[name].saved

    def save_settings(self):
        settings_dict = {}
        for name, setting in self.settings_dto.items():
            if setting.saved:
                settings_dict.update({name: setting.value})
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
        self._create_entered_variable('normal_font', ("Verdana", 10))
        self._create_entered_variable('fig_dpi', 100)
        self._create_entered_variable('init_directory', "../iniFiles/")
        self._create_entered_variable('input_file', "../instructions_fromFLIMage.txt")
        self._create_entered_variable('output_file', "../instructions_fromSpineTracker.txt")

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
        self._create_gui_variable('duration', tk.StringVar, False, 5, dtype=np.int)
        self._create_gui_variable('period', tk.StringVar, False, 60, dtype=np.int)
        self._create_gui_variable('step_name', tk.StringVar, False, "StepName")
        self._create_gui_variable('training_data_path', tk.StringVar, True, '../test')
        self._create_gui_variable('new_model_path', tk.StringVar, True, '../test')
        self._create_gui_variable('test_data_path', tk.StringVar, True, '../test')
        self._create_gui_variable('yolo_image_path', tk.StringVar, True, '../test.tif')
        self._create_gui_variable('trained_model_path', tk.StringVar, True,
                                  'spine_yolo/model_data/trained_stage_3_best.h5')

    def initialize_acquired_variables(self):
        self._create_acquired_variable('fov_x_y', np.array([250, 250]), dtype=np.float32)
        self._create_acquired_variable('scan_voltage_multiplier', np.array([1, 1]), dtype=np.float32)
        self._create_acquired_variable('scan_voltage_range_reference', np.array([15, 15]), dtype=np.float32)
        self._create_acquired_variable('macro_image', np.zeros([128, 128]), dtype=np.uint8)
        self._create_acquired_variable('image_file_path', '../test/test_image.tif')
        self._create_acquired_variable('current_zoom', 1, dtype=np.int)
        self._create_acquired_variable('z_slice_num', np.array([0]), dtype=np.int)
        self._create_acquired_variable('resolution_x_y', np.array([0]), dtype=np.int)

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


class Setting:

    def __init__(self, name, gui_var, saved, default, callback=None, dtype=None):
        self.name = name
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
            self.value = blank_to_zero(self.value)
            if self.value is not None:
                try:
                    self.value = np.array([self.value], dtype=self.dtype)
                except ValueError as err:
                    self.value = np.array(0, dtype=self.dtype)
                    print(err)

    def set(self, value):
        self.value = value
        self._update_dtype()
        self.update_gui()

    def get_value(self):
        val = self.value
        if (type(self.value) is np.ndarray) and (len(self.value) == 1):
            val = self.value.item(0)
        return val

    def update_gui(self):
        if self.gui_var is not None:
            # print('var: {}, value: {}'.format(self.gui_var, self.value))
            value = none_to_blank(self.get_value())
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
            args = args[0][0]
            if len(args) != 0:
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
