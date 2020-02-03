import os
import re

import numpy as np

from app.Coordinates import Coordinates


class Position(dict):
    def __init__(self):
        super().__init__()
        self['coordinates'] = None
        self['ref_image'] = None
        self['ref_image_zoomed_out'] = None
        self['roi_x_y'] = None
        self['af_box_xywh'] = None
        self['rotation'] = 0
        self['zoom'] = 10
        self['fov_xy'] = np.array([250, 250])
        self['scan_voltage_multiplier'] = np.array([1, 1])
        self['zstep'] = 1
        self['collected_files'] = []
        self['drift_history'] = []

    def get_ref_image_side(self):
        return self['ref_image'].shape[0]

    def get_ref_image_zoomed_out_side(self):
        return self['ref_image'].shape[0]

    def save(self):
        position_to_save = Position()
        for key in self:
            if getattr(self[key], 'save', None):
                position_to_save[key] = self[key].save()
            else:
                position_to_save[key] = self[key]
        return position_to_save

    def clear_file_names(self):
        self['collected_files'] = []

    def add_file_path(self, path):
        self['collected_files'].append(path)

    def load(self, loaded_position, center_coordinates):
        for key in loaded_position:
            if key == 'coordinates':
                self[key] = center_coordinates.copy()
                self[key].load(loaded_position[key])
            else:
                self[key] = loaded_position[key]

    def set_coordinates(self, coordinates):
        self['coordinates'] = coordinates

    def set_ref_image(self, ref_image):
        self['ref_image'] = ref_image.copy()

    def set_ref_image_zoomed_out(self, ref_image_zoomed_out):
        self['ref_image_zoomed_out'] = ref_image_zoomed_out.copy()

    def set_roi_x_y(self, roi_x_y):
        self['roi_x_y'] = roi_x_y

    def get_roi_x_y(self):
        return self['roi_x_y']

    def get_ref_image(self):
        return self['ref_image']

    def get_ref_image_zoomed_out(self):
        return self['ref_image_zoomed_out']

    def record_drift_history(self, drift_x_y_z):
        self['drift_history'].append(drift_x_y_z)

    def set_default_roi_pos(self):
        roi_x_y = np.array(self['ref_image'].get_shape()[:2]) / 2
        self['roi_x_y'] = roi_x_y

    def rename_file(self, pos_id):
        path, file = os.path.split(self['collected_files'][-1])
        parent_dir = os.path.dirname(path)  # assumes we're looking in parent dir
        file_number, associated_files = self.get_associated_files(parent_dir, file)
        number_extractor = re.compile(file_number)
        file_length = len(self['collected_files'])
        new_number = f'{file_length:04d}'
        for file_to_rename in associated_files:
            old_path = os.path.join(parent_dir, file_to_rename)
            file_with_new_number = number_extractor.sub(new_number, file_to_rename)
            new_file_name = f'position_{pos_id}_{file_with_new_number}'
            file_path_new = os.path.join(parent_dir, new_file_name)
            try:
                os.rename(old_path, file_path_new)
            except FileExistsError:
                pass

    @staticmethod
    def get_associated_files(path, file):
        associated_files = []
        number_extractor = re.compile('([0-9]+)(?:.tif)')
        file_number = number_extractor.search(file).group(1)
        all_files_in_folder = os.listdir(path)
        for file_in_folder in all_files_in_folder:
            if file_number in file_in_folder:
                associated_files.append(file_in_folder)
        return file_number, associated_files