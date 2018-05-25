import getopt
import os
import pickle
import tkinter as tk
import numpy as np
import sys

from app.inherited.inherited.inherited.inherited.SpineTrackerContainer import SpineTrackerContainer
from utilities.math_helpers import float_or_none


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

        # Settings set in command line
        self._create_command_line_variable('simulation', False)
        self._create_command_line_variable('verbose', False)

        # Settings set in guis
        self._create_gui_variable('stagger', tk.StringVar, True, 5,
                                  callback=self.container.stagger_string_var_callback, dtype=np.int)
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
                                  callback=self.container.image_or_uncage_string_var_callback)
        self._create_variable('exclusive', tk.BooleanVar, False, False)
        self._create_variable('duration', tk.StringVar, False, 5, dtype=np.int)
        self._create_variable('period', tk.StringVar, False, 60, dtype=np.int)
        self._create_variable('step_name', tk.StringVar, False, "StepName")

        # Settings gotten from imaging program
        self._create_acquired_variable('fov_x_y', np.array([250, 250]), dtype=np.float32)
        self._create_acquired_variable('scan_angle_multiplier', np.array([1, 1]), dtype=np.float32)
        self._create_acquired_variable('scan_angle_range_reference', np.array([15, 15]), dtype=np.float32)
        self._create_acquired_variable('current_zoom', None, dtype=np.int)
        self._create_acquired_variable('center_xyz', np.array([0,0,0]), dtype=np.float32)
        self._create_acquired_variable('center_coordinates', np.array([0,0,0]), dtype=np.float32)
        self._create_acquired_variable('center_scan_angle_x_y', np.array([0,0]), dtype=np.float32)
        self._create_acquired_variable('macro_image', np.zeros([128,128]), dtype=np.uint8)



        # self['experiment_log_file'] = Setting('experiment_log_file', None, False, '../temp/experiment_log.txt')
        # self['large_font'] = Setting('large_font', None, False, ("Verdana", 12))
        # self['fig_dpi'] = Setting('fig_dpi', None, False, 100)
        # self['init_directory'] = Setting('init_directory', False, False, "../iniFiles/")
        #
        # # Settings set in command line
        # self['simulation'] = Setting('simulation', None, False, False)
        # self['verbose'] = Setting('verbose', False, False, False)
        #
        # # Settings set in guis
        # self['stagger'] = Setting('stagger', tk.StringVar(container), True, 5,
        #                           callback=self.container.stagger_string_var_callback, dtype=np.int)
        # self['drift_correction_channel'] = Setting('drift_correction_channel', tk.StringVar(container), True, 1, dtype=np.int)
        # self['total_channels'] = Setting('total_channels', tk.StringVar(container), True, 2, dtype=np.int)
        # self['imaging_zoom'] = Setting('imaging_zoom', tk.StringVar(container), True, 30, dtype=np.int)
        # self['imaging_slices'] = Setting('imaging_slices', tk.StringVar(container), True, 3, dtype=np.int)
        # self['reference_zoom'] = Setting('reference_zoom', tk.StringVar(container), True, 10, dtype=np.int)
        # self['reference_slices'] = Setting('reference_slices', tk.StringVar(container), True, 10, dtype=np.int)
        # self['park_xy_motor'] = Setting('park_xy_motor', tk.BooleanVar(container), True, True)
        # self['macro_resolution_x'] = Setting('macro_resolution_x', tk.StringVar(container), True, 512, dtype=np.int)
        # self['macro_resolution_y'] = Setting('macro_resolution_y', tk.StringVar(container), True, 512, dtype=np.int)
        # self['normal_resolution_x'] = Setting('normal_resolution_x', tk.StringVar(container), True, 128, dtype=np.int)
        # self['normal_resolution_y'] = Setting('normal_resolution_y', tk.StringVar(container), True, 128, dtype=np.int)
        # self['macro_zoom'] = Setting('macro_zoom', tk.StringVar(container), True, 1, dtype=np.int)
        # self['macro_z_slices'] = Setting('macro_z_slices', tk.StringVar(container), True, 10, dtype=np.int)
        # self['uncaging_roi_toggle'] = Setting('uncaging_roi_toggle', tk.BooleanVar(container), True, False)
        # self['image_or_uncage'] = Setting('image_or_uncage', tk.StringVar(container), False, 'Image',
        #                                   callback=self.container.image_or_uncage_string_var_callback)
        # self['exclusive'] = Setting('exclusive', tk.BooleanVar(container), False, False)
        # self['duration'] = Setting('duration', tk.StringVar(container), False, 5, dtype=np.int)
        # self['period'] = Setting('period', tk.StringVar(container), False, 60, dtype=np.int)
        # self['step_name'] = Setting('step_name', tk.StringVar(container), False, "StepName")
        #
        # # Settings gotten from imaging program
        # self['fov_x_y'] = Setting('fov_x_y', None, False, np.array([250, 250]), dtype=np.float32)
        # self['scan_angle_multiplier'] = Setting('scan_angle_multiplier', None, False, np.array([1, 1]), dtype=np.float32)
        # self['scan_angle_range_reference'] = Setting('scan_angle_range_reference', None, False, np.array([15, 15]), dtype=np.float32)

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
            self.value = float_or_none(self.value)
            self.value = np.array(self.value, dtype=self.dtype)

    def set(self, value):
        self.value = value
        self._update_dtype()
        self.update_gui()

    def update_gui(self):
        if self.gui_var is not None:
            self.gui_var.set(self.value)

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


class SettingsManager:

    def __init__(self, container):
        self.settings_dto = SettingsDTO(container)
        self.set_default_traces()

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


class Initializer(SpineTrackerContainer):

    def __init__(self, *args, **kwargs):
        super(Initializer, self).__init__()
        self.settings = SettingsManager(self)
        self.command_line_interpreter = CommandLineInterpreter(self.settings, *args)
        self.command_line_interpreter.interpret()


# class SpineTrackerSettings(SpineTrackerContainer):

    # def __init__(self, *args, **kwargs):
    #     super(SpineTrackerSettings, self).__init__()
    #     self.settings = dict()
    #     self.acq = dict()
    #     self.app_params = dict(large_font=("Verdana", 12),
    #                            fig_dpi=100,
    #                            simulation=False,
    #                            verbose=False,
    #                            init_directory="../iniFiles/")
    #     self.interpret_command_line_arguments(args)
    #     self.gui_vars = dict(
    #         stagger_string_var=tk.StringVar(self),
    #         image_or_uncage_string_var=tk.StringVar(self),
    #         exclusive_bool_var=tk.BooleanVar(self),
    #         duration_string_var=tk.StringVar(self),
    #         period_string_var=tk.StringVar(self),
    #         step_name_string_var=tk.StringVar(self),
    #         macro_zoom_string_var=tk.StringVar(self),
    #         macro_z_slices_string_var=tk.StringVar(self),
    #         total_channels_string_var=tk.StringVar(self),
    #         drift_correction_channel_string_var=tk.StringVar(self),
    #         park_xy_motor_bool_var=tk.BooleanVar(self),
    #         uncaging_roi_toggle_bool_var=tk.BooleanVar(self),
    #         macro_resolution_x_string_var=tk.StringVar(self),
    #         macro_resolution_y_string_var=tk.StringVar(self),
    #         normal_resolution_x_string_var=tk.StringVar(self),
    #         normal_resolution_y_string_var=tk.StringVar(self),
    #         imaging_zoom_string_var=tk.StringVar(self),
    #         reference_zoom_string_var=tk.StringVar(self),
    #         imaging_slices_string_var=tk.StringVar(self),
    #         reference_slices_string_var=tk.StringVar(self))
    #
    #     # Translate corresponding settings to their GUI variables
    #     self.settings_to_gui_vars = dict(
    #         drift_correction_channel='drift_correction_channel_string_var',
    #         stagger='stagger_string_var',
    #         total_channels='total_channels_string_var',
    #         imaging_zoom='imaging_zoom_string_var',
    #         imaging_slices='imaging_slices_string_var',
    #         reference_zoom='reference_zoom_string_var',
    #         reference_slices='reference_slices_string_var',
    #         park_xy_motor='park_xy_motor_bool_var',
    #         macro_resolution_x='macro_resolution_x_string_var',
    #         macro_resolution_y='macro_resolution_y_string_var',
    #         normal_resolution_x='normal_resolution_x_string_var',
    #         normal_resolution_y='normal_resolution_y_string_var',
    #         macro_zoom='macro_zoom_string_var',
    #         macro_z_slices='macro_z_slices_string_var',
    #         uncaging_roi_toggle='uncaging_roi_toggle_bool_var')
    #
    #     # Load Settings
    #     self.load_settings()
    #
    #     # Set Values
    #     self.gui_vars['image_or_uncage_string_var'].set("Image")
    #     self.update_gui_from_settings()
    #
    #     # Set add trace functions
    #     # Special Callbacks
    #     self.gui_vars['image_or_uncage_string_var'].trace_add('write', self.image_or_uncage_string_var_callback)
    #     self.gui_vars['stagger_string_var'].trace_add('write', self.stagger_string_var_callback)
    #     # Generic Callbacks
    #     gui_keys = ['imaging_zoom_string_var',
    #                 'uncaging_roi_toggle_bool_var',
    #                 'reference_zoom_string_var',
    #                 'imaging_slices_string_var',
    #                 'reference_slices_string_var',
    #                 'park_xy_motor_bool_var',
    #                 'total_channels_string_var',
    #                 'macro_resolution_x_string_var',
    #                 'macro_resolution_y_string_var',
    #                 'normal_resolution_x_string_var',
    #                 'normal_resolution_y_string_var',
    #                 'stagger_string_var',
    #                 'macro_zoom_string_var',
    #                 'macro_z_slices_string_var',
    #                 'uncaging_roi_toggle_bool_var']
    #
    #     for key in gui_keys:
    #         self.gui_vars[key].trace_add('write', self.update_settings_from_gui)

    # def interpret_command_line_arguments(self, args):
    #     if args:
    #         args = args[0]
    #         try:
    #             options, remainder = getopt.getopt(args, 'sv', ['simulation', 'verbose'])
    #         except getopt.GetoptError:
    #             print('Error - incorrect input format')
    #             print('correct Format: main.py -v -s')
    #             sys.exit(2)
    #         for opt, val in options:
    #             if opt in ('-s', '--simulation'):
    #                 print('simulation mode on')
    #                 self.set_app_param('simulation', True)
    #             elif opt in ('-v', '--verbose'):
    #                 print('verbose mode on')
    #                 self.set_app_param('verbose', True)

    # def load_settings(self):
    #     file_name = self.get_app_param('init_directory') + 'user_settings.p'
    #     if os.path.isfile(file_name):
    #         self.settings = pickle.load(open(file_name, 'rb'))
    #     self.add_missing_settings()

    # def add_missing_settings(self):
    #     default_settings = {'drift_correction_channel': 1,
    #                         'fov_x_y': np.array([250, 250]),
    #                         'experiment_log_file': '../temp/experiment_log.txt',
    #                         'scan_angle_multiplier': np.array([1, 1]),
    #                         'scan_angle_range_reference': np.array([15, 15]),
    #                         'stagger': 10,
    #                         'total_channels': 2,
    #                         'imaging_zoom': 30,
    #                         'imaging_slices': 3,
    #                         'reference_zoom': 15,
    #                         'reference_slices': 10,
    #                         'park_xy_motor': True,
    #                         'macro_resolution_x': 512,
    #                         'macro_resolution_y': 512,
    #                         'normal_resolution_x': 128,
    #                         'normal_resolution_y': 128,
    #                         'macro_z_slices': 10,
    #                         'macro_zoom': 1,
    #                         'uncaging_roi_toggle': True
    #                         }
    #     flag = False
    #     for key in default_settings:
    #         if key not in self.settings.keys():
    #             self.settings[key] = default_settings[key]
    #             flag = True
    #     if flag:
    #         self.save_settings()

    # def save_settings(self):
    #     user_settings = self.settings
    #     pickle.dump(user_settings, open(self.get_app_param('init_directory') + 'user_settings.p', 'wb'))

    # def update_settings_from_gui(self, a=None, b=None, c=None, settings_key=None):
    #     save_settings_flag = False
    #     if not settings_key:
    #         for settings_key, gui_var_key in self.settings_to_gui_vars.items():
    #             val = self.gui_vars[gui_var_key].get()
    #             if self.settings[settings_key] != val:
    #                 self.settings[settings_key] = val
    #                 save_settings_flag = True
    #     else:
    #         self.settings[settings_key] = self.gui_vars[self.settings_to_gui_vars[settings_key]].get()
    #         save_settings_flag = True
    #     if save_settings_flag:
    #         self.save_settings()

    # def update_gui_from_settings(self, settings_key=None):
    #     if not settings_key:
    #         for settings_key, gui_var_key in self.settings_to_gui_vars.items():
    #             self.gui_vars[gui_var_key].set(self.settings[settings_key])
    #     else:
    #         gui_var_key = self.settings_to_gui_vars[settings_key]
    #         self.gui_vars[gui_var_key].set(self.settings[settings_key])

    # def get_app_param(self, k, *args):
    #     param = self.app_params.get(k, None)
    #     if param is None and args:
    #         param = args[0]
    #     return param

    # def get_settings(self, k, *args):
    #     setting = self.settings.get(k, None)
    #     if setting is None and args:
    #         setting = args[0]
    #     return setting

    # def set_settings(self, k, v):
    #     self.settings[k] = v
    #     self.save_settings()

    # def set_app_param(self, k, v):
    #     self.app_params[k] = v

    # def update_settings_from_source(self, key, source):
    #     self.set_settings(key, source.get())

    # def get_acq_var(self, k, *args):
    #     var = self.acq.get(k, None)
    #     if var is None and args:
    #         var = args[0]
    #     return var

    # def set_acq_var(self, k, v):
    #     self.acq[k] = v

    # def load_test_ref_image(self):  # for testing purposes only
    #     pass
