import os

import pickle

import numpy as np


class PositionsManager:

    def __init__(self, settings):
        self.settings = settings
        self.positions = Positions()

    def load_previous_positions(self):
        file_name = self.settings.get('init_directory') + 'positions.p'
        self.positions.load_positions_from_file(file_name)

    def get_roi_x_y(self, pos_id):
        roi_x, roi_y = self.positions[pos_id]['roi_x_y']
        return roi_x, roi_y

    def create_new_pos(self, ref_image, ref_image_zoomed_out):
        xyz = self.settings.get('current_combined_coordinates')
        pos_id = self.positions.initialize_new_position()
        self.positions.set_coordinates(pos_id, xyz)
        self.positions[pos_id].set_ref_image(ref_image)
        self.positions[pos_id].set_ref_image_zoomed_out(ref_image_zoomed_out)
        self.positions[pos_id].set_default_roi_pos()

    def clear(self):
        self.positions = Positions()

    def remove(self, pos_id):
        del self.positions[pos_id]

    def backup_positions(self):
        positions = self.positions
        pickle.dump(positions, open(self.settings.get('init_directory') + 'positions.p', 'wb'))

    def record_drift_history_of_acquired_image(self, acquired_image):
        pos_id = acquired_image.pos_id
        drift_x_y_z = acquired_image.drift_x_y_z.copy()
        self.positions[pos_id].record_drift_history(drift_x_y_z)


class Positions(dict):

    def __init__(self):
        super(Positions, self).__init__()

    def load_positions_from_file(self, file_name):
        if os.path.isfile(file_name):
            positions_dict = pickle.load(open(file_name, 'rb'))
            for pos_id, position in positions_dict.items():
                self[pos_id] = position

    def initialize_new_position(self):
        pos_id = self._get_next_pos_id()
        self[pos_id] = Position()
        return pos_id

    def _get_next_pos_id(self):
        max_pos_id = 1
        for key in self:
            if key >= max_pos_id:
                max_pos_id = key + 1
        return max_pos_id

    def set_coordinates(self, pos_id, xyz):
        self[pos_id].set_coordinates(xyz)


class Position:
    def __init__(self):
        self.coordinates = {'x': 0, 'y': 0, 'z': 0}
        self.ref_image = None
        self.ref_image_zoomed_out = None
        self.roi_x_y = None
        self.drift_history = []

    def set_coordinates(self, xyz):
        self.coordinates.update(xyz)

    def set_ref_image(self, ref_image):
        self.ref_image = ref_image

    def set_ref_image_zoomed_out(self, ref_image_zoomed_out):
        self.ref_image_zoomed_out = ref_image_zoomed_out

    def set_roi_x_y(self, roi_x_y):
        self.roi_x_y = roi_x_y

    def get_ref_image(self):
        return self.ref_image

    def get_ref_image_zoomed_out(self):
        return self.ref_image_zoomed_out

    def record_drift_history(self, drift_x_y_z):
        self.drift_history.append(drift_x_y_z)

    def set_default_roi_pos(self):
        roi_x_y = np.array(self.ref_image.get_shape()[:2]) / 2
        self.roi_x_y = roi_x_y
