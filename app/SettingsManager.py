import os
import pickle

# TODO: Check if container has to be the giu for creating gui vars, or if it can just be the main app
from app.SettingsDTO import SettingsDTO


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
            self.container.rebuild_timeline()
        elif name == 'image_or_uncage':
            self.container.switch_between_image_and_uncage_guis()
        elif name == 'manual_fov_toggle':
            self.container.toggle_manual_fov_entering()
        elif name == 'training_data_path':
            self.container.show_end_of_path()
        elif name == 'trained_model_path':
            self.container.show_end_of_path()
        elif name == 'pipe_connect_bool':
            self.container.toggle_pipe_connection()
        if self.setting_is_saved(name):
            self.save_settings()
            # TODO: Maybe add a save method to all classes where info needs to be saved, so as to avoid the session/settings/pickle issue. \
            # Or just create a save class that saves a specific list of variables or something....

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
        # else:
        #     # TODO: Add error handling here?
        #     print('Variable {} does not exist. Declare all variables first in SettingsDTO'.format(name))

    def get(self, name):
        if self._exists(name):
            return self.settings_dto[name].get_value()

    def get_gui_var(self, name):
        return self.settings_dto[name].gui_var

    def assign_settings(self, settings_dict):
        for key in settings_dict:
            settings_dict[key] = self.get(key)

    def assign_gui_vars(self, gui_vars_dict):
        for key in gui_vars_dict:
            gui_vars_dict[key] = self.get_gui_var(key)

    def load_settings(self, path=None):
        if path is None:
            path = self._get_file_name()
        if os.path.isfile(path):
            settings_dict = pickle.load(open(path, 'rb'))
            self.update_with_loaded_dict(settings_dict)

    def update_with_loaded_dict(self, settings_dict):
        for name, value in settings_dict.items():
            self.set(name, value)

    def setting_is_saved(self, name):
        return self.settings_dto[name].saved

    def save_settings(self, path=None):
        if path is None:
            path = self._get_file_name()
        settings_dict = {}
        for name, setting in self.settings_dto.items():
            if setting.saved:
                settings_dict.update({name: setting.value})
        pickle.dump(settings_dict, open(path, 'wb'))

    def _get_file_name(self):
        return self.get('init_directory') + 'user_settings.p'

    def update_gui_from_settings(self, name=None):
        if not name:
            for name, setting in self.settings_dto.items():
                setting.update_gui()
        else:
            self.settings_dto[name].update_gui()


