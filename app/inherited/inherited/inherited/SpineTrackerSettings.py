import os
import pickle
import tkinter as tk

from app.inherited.inherited.inherited.inherited.SpineTrackerContainer import SpineTrackerContainer


class SpineTrackerSettings(SpineTrackerContainer):

    def __init__(self, *args, **kwargs):
        super(SpineTrackerSettings, self).__init__(*args, **kwargs)
        self.settings = dict()
        self.acq = dict()
        self.app_params = dict(large_font=("Verdana", 12),
                               fig_dpi=100,
                               simulation=True,
                               verbose=True,
                               initDirectory="../iniFiles/")

        self.gui_vars = dict(
            stagger_string_var=tk.StringVar(self),
            image_or_uncage_string_var=tk.StringVar(self),
            exclusive_bool_var=tk.BooleanVar(self),
            duration_string_var=tk.StringVar(self),
            period_string_var=tk.StringVar(self),
            step_name_string_var=tk.StringVar(self),
            macro_zoom_string_var=tk.StringVar(self),
            num_z_slices_string_var=tk.StringVar(self),
            total_channels_string_var=tk.StringVar(self),
            drift_correction_channel_string_var=tk.StringVar(self),
            park_xy_motor_bool_var=tk.BooleanVar(self),
            uncaging_roi_toggle_bool_var=tk.BooleanVar(self),
            macro_resolution_x_string_var=tk.StringVar(self),
            macro_resolution_y_string_var=tk.StringVar(self),
            normal_resolution_x_string_var=tk.StringVar(self),
            normal_resolution_y_string_var=tk.StringVar(self),
            imaging_zoom_string_var=tk.StringVar(self),
            reference_zoom_string_var=tk.StringVar(self),
            imaging_slices_string_var=tk.StringVar(self),
            reference_slices_string_var=tk.StringVar(self))

        # Translate corresponding settings to their GUI variables
        self.settings_to_gui_vars = dict(
            drift_correction_channel='drift_correction_channel_string_var',
            stagger='stagger_string_var',
            total_channels='total_channels_string_var',
            imaging_zoom='imaging_zoom_string_var',
            imaging_slices='imaging_slices_string_var',
            reference_zoom='reference_zoom_string_var',
            reference_slices='reference_slices_string_var',
            park_xy_motor='park_xy_motor_bool_var',
            macro_resolution_x='macro_resolution_x_string_var',
            macro_resolution_y='macro_resolution_y_string_var',
            normal_resolution_x='normal_resolution_x_string_var',
            normal_resolution_y='normal_resolution_y_string_var',
            macro_zoom='macro_zoom_string_var',
            num_z_slices='num_z_slices_string_var',
            uncaging_roi_toggle='uncaging_roi_toggle_bool_var')

        # Load Settings
        self.load_settings()

        # Set Values
        self.gui_vars['image_or_uncage_string_var'].set("Image")
        self.update_gui_from_settings()

        # Set add trace functions
        # Special Callbacks
        self.gui_vars['image_or_uncage_string_var'].trace_add('write', self.image_or_uncage_string_var_callback)
        self.gui_vars['stagger_string_var'].trace_add('write', self.stagger_string_var_callback)
        # Generic Callbacks
        gui_keys = ['imaging_zoom_string_var',
                    'uncaging_roi_toggle_bool_var',
                    'reference_zoom_string_var',
                    'imaging_slices_string_var',
                    'reference_slices_string_var',
                    'park_xy_motor_bool_var',
                    'total_channels_string_var',
                    'macro_resolution_x_string_var',
                    'macro_resolution_y_string_var',
                    'normal_resolution_x_string_var',
                    'normal_resolution_y_string_var',
                    'stagger_string_var',
                    'macro_zoom_string_var',
                    'num_z_slices_string_var',
                    'uncaging_roi_toggle_bool_var']

        for key in gui_keys:
            self.gui_vars[key].trace_add('write', self.update_settings_from_gui)

    def load_settings(self):
        file_name = self.get_app_param('initDirectory') + 'user_settings.p'
        if os.path.isfile(file_name):
            self.settings = pickle.load(open(file_name, 'rb'))
        self.add_missing_settings()

    def add_missing_settings(self):
        default_settings = {'drift_correction_channel': 1,
                            'fov_x_y': (250, 250),
                            'stagger': 10,
                            'total_channels': 2,
                            'imaging_zoom': 30,
                            'imaging_slices': 3,
                            'reference_zoom': 15,
                            'reference_slices': 10,
                            'park_xy_motor': True,
                            'macro_resolution_x': 512,
                            'macro_resolution_y': 512,
                            'normal_resolution_x': 128,
                            'normal_resolution_y': 128,
                            'num_z_slices': 10,
                            'macro_zoom': 1,
                            'uncaging_roi_toggle': True
                            }
        flag = False
        for key in default_settings:
            if key not in self.settings.keys():
                self.settings[key] = default_settings[key]
                flag = True
        if flag:
            self.save_settings()

    def save_settings(self):
        user_settings = self.settings
        pickle.dump(user_settings, open(self.get_app_param('initDirectory') + 'user_settings.p', 'wb'))

    def update_settings_from_gui(self, a=None, b=None, c=None, settings_key=None):
        save_settings_flag = False
        if a:
            # TODO: Identify gui_var_key based on a
            pass
        if not settings_key:
            for settings_key, gui_var_key in self.settings_to_gui_vars.items():
                val = self.gui_vars[gui_var_key].get()
                if self.settings[settings_key] != val:
                    self.settings[settings_key] = val
                    save_settings_flag = True
        else:
            self.settings[settings_key] = self.gui_vars[self.settings_to_gui_vars[settings_key]].get()
            save_settings_flag = True
        if save_settings_flag:
            self.save_settings()

    def update_gui_from_settings(self, settings_key=None):
        # TODO: Going to have to deal with all these string/int/double/boolean conversions somehow
        if not settings_key:
            for settings_key, gui_var_key in self.settings_to_gui_vars.items():
                self.gui_vars[gui_var_key].set(self.settings[settings_key])
        else:
            gui_var_key = self.settings_to_gui_vars[settings_key]
            self.gui_vars[gui_var_key].set(self.settings[settings_key])

    def get_app_param(self, k, *args):
        param = self.app_params.get(k, None)
        if param is None and args:
            param = args[0]
        return param

    def get_settings(self, k, *args):
        setting = self.settings.get(k, None)
        if setting is None and args:
            setting = args[0]
        return setting

    def set_settings(self, k, v):
        self.settings[k] = v
        self.save_settings()

    def set_app_param(self, k, v):
        self.app_params[k] = v

    def update_settings_from_source(self, key, source):
        self.set_settings(key, source.get())

    def get_acq_var(self, k, *args):
        var = self.acq.get(k, None)
        if var is None and args:
            var = args[0]
        return var

    def set_acq_var(self, k, v):
        self.acq[k] = v

    def load_test_ref_image(self):  # for testing purposes only
        pass
