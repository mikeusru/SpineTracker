import os
import pickle
from app.inherited.SpineTrackerContainer import SpineTrackerContainer


class SpineTrackerSettings(SpineTrackerContainer):

    def __init__(self, *args, **kwargs):
        super(SpineTrackerSettings, self).__init__(*args, **kwargs)
        self.settings = {}
        self.acq = {}
        self.app_params = dict(large_font=("Verdana", 12),
                               fig_dpi=100,
                               simulation=True,
                               verbose=True,
                               initDirectory="../iniFiles/")
        self.load_settings()

    def set_app_param(self, k, v):
        self.app_params[k] = v

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

    def save_settings(self):
        user_settings = self.settings
        pickle.dump(user_settings, open(self.get_app_param('initDirectory') + 'user_settings.p', 'wb'))

    def load_settings(self):
        file_name = self.get_app_param('initDirectory') + 'user_settings.p'
        if os.path.isfile(file_name):
            self.settings = pickle.load(open(file_name, 'rb'))
        self.add_default_settings()

    def add_default_settings(self):
        default_settings = {'driftCorrectionChannel': 1,
                            'fovXY': (250, 250),
                            'stagger': 10,
                            'totalChannels': 2,
                            'imagingZoom': 30,
                            'imagingSlices': 3,
                            'referenceZoom': 15,
                            'referenceSlices': 10,
                            'park_xy_motor': True
                            }
        flag = False
        for key in default_settings:
            if key not in self.settings.keys():
                self.settings[key] = default_settings[key]
                flag = True
        if flag:
            self.save_settings()

    def get_acq_var(self, k, *args):
        var = self.acq.get(k, None)
        if var is None and args:
            var = args[0]
        return var

    def set_acq_var(self, k, v):
        self.acq[k] = v

    def update_settings_from_source(self, key, source):
        self.set_settings(key, source.get())