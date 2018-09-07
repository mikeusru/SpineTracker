import os

import pickle

import numpy as np


class Positions(dict):

    def __init__(self, session):
        super(Positions, self).__init__()
        self.settings = session.settings
        self.session = session

    def get_image(self, pos_id, zoomed_out=False):
        if zoomed_out:
            ref_img = self[pos_id].get_ref_image_zoomed_out()
        else:
            ref_img = self[pos_id].get_ref_image()
        return ref_img

    def get_roi_x_y(self, pos_id):
        roi_x, roi_y = self[pos_id].get_roi_x_y()
        return roi_x, roi_y

    def get_average_coordinate(self):
        x_list = []
        y_list = []
        z_list = []
        for pos_id in self:
            coordinates = self.get_coordinates(pos_id)
            xyz = coordinates.get_combined(self.session)
            x_list.append(xyz['x'])
            y_list.append(xyz['y'])
            z_list.append(xyz['z'])
        x_average = np.average(np.array(x_list))
        y_average = np.average(np.array(y_list))
        z_average = np.average(np.array(z_list))
        return dict(x=x_average, y=y_average, z=z_average)

    def update_all_coordinates_relative_to_center(self):
        for pos_id in self:
            self[pos_id].coordinates.update_to_center(self.session)

    def create_new_pos(self, ref_image, ref_image_zoomed_out):
        coordinates = self.session.state.current_coordinates.copy()
        pos_id = self.initialize_new_position()
        self.set_coordinates(pos_id, coordinates)
        self[pos_id].set_ref_image(ref_image)
        self[pos_id].set_ref_image_zoomed_out(ref_image_zoomed_out)
        self[pos_id].set_default_roi_pos()

    def clear(self):
        keys = [pos_id for pos_id in self]
        for pos_id in keys:
            self.remove(pos_id)

    def remove(self, pos_id):
        del self[pos_id]

    def backup_positions(self):
        positions_dict = {}
        for key, val in self.items():
            positions_dict.update({key: val})
        pickle.dump(positions_dict, open(self.settings.get('init_directory') + 'positions.p', 'wb'))

    def record_drift_history_of_acquired_image(self, acquired_image):
        pos_id = acquired_image.pos_id
        drift_x_y_z = acquired_image.drift_x_y_z.copy()
        self[pos_id].record_drift_history(drift_x_y_z)

    def load_previous_positions(self):
        file_name = self.settings.get('init_directory') + 'positions.p'
        try:
            if os.path.isfile(file_name):
                positions_dict = pickle.load(open(file_name, 'rb'))
                for pos_id, position in positions_dict.items():
                    self[pos_id] = position
        except EOFError as err:
            print(f'Error loading positions: {err}')

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

    def set_coordinates(self, pos_id, coordinates):
        self[pos_id].set_coordinates(coordinates)

    def get_coordinates(self, pos_id):
        coordinates = self[pos_id].coordinates
        return coordinates

    def update_coordinates_for_drift(self, pos_id, drift_x_y_z):
        self[pos_id].coordinates.update_to_drift(drift_x_y_z, self.session)


class Position:
    def __init__(self):
        self.coordinates = None
        self.ref_image = None
        self.ref_image_zoomed_out = None
        self.roi_x_y = None
        self.drift_history = []

    def save(self):
        return dict(
            coordinates=self.coordinates.save(),
            ref_image=self.ref_image,
            roi_x_y=self.roi_x_y,
            drift_history=self.drift_history,
        )

    def load(self, loaded_position):
        self.coordinates.load(loaded_position['coordinates']),
        self.ref_image = loaded_position['ref_image']
        self.roi_x_y = loaded_position['roi_x_y']
        self.drift_history = loaded_position['drift_history']

    def set_coordinates(self, coordinates):
        self.coordinates = coordinates

    def set_ref_image(self, ref_image):
        self.ref_image = ref_image.copy()

    def set_ref_image_zoomed_out(self, ref_image_zoomed_out):
        self.ref_image_zoomed_out = ref_image_zoomed_out.copy()

    def set_roi_x_y(self, roi_x_y):
        self.roi_x_y = roi_x_y

    def get_roi_x_y(self):
        return self.roi_x_y

    def get_ref_image(self):
        return self.ref_image

    def get_ref_image_zoomed_out(self):
        return self.ref_image_zoomed_out

    def record_drift_history(self, drift_x_y_z):
        self.drift_history.append(drift_x_y_z)

    def set_default_roi_pos(self):
        roi_x_y = np.array(self.ref_image.get_shape()[:2]) / 2
        self.roi_x_y = roi_x_y
