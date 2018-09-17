import os

import pickle

import numpy as np


class Positions(dict):

    def __init__(self, session):
        super(Positions, self).__init__()
        self.settings = session.settings
        self.session = session
        self.current_position = 0

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
        self.current_position = pos_id

    def update_refs(self, pos_id, ref_image, ref_image_zoomed_out):
        self[pos_id].set_ref_image(ref_image)
        self[pos_id].set_ref_image_zoomed_out(ref_image_zoomed_out)

    def clear(self):
        keys = [pos_id for pos_id in self]
        for pos_id in keys:
            self.remove(pos_id)
        self.current_position = 0

    def remove(self, pos_id):
        del self[pos_id]
        pos_id = 0
        for key in self:
            pos_id = key
        self.current_position = pos_id

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
                self.current_position = pos_id
        except EOFError as err:
            print(f'Error loading positions: {err}')

    def initialize_new_position(self):
        pos_id = self._get_next_pos_id()
        self[pos_id] = Position()
        self.current_position = pos_id
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

    def import_parameters_from_session(self, pos_id):
        if pos_id in self:
            settings = self.session.settings
            position = self[pos_id]
            position.zoom = float(settings.get('imaging_zoom'))
            position.scan_voltage_multiplier = np.array(settings.get('scan_voltage_multiplier'))
            position.scan_voltage_range_reference = np.array(settings.get('scan_voltage_range_reference'))
            position.rotation = float(settings.get('rotation'))
            position.fovxy = np.squeeze(np.array([settings.get('fov_x'), settings.get('fov_y')]))
            position.zstep = float(settings.get('zstep'))

    def export_parameters_to_session(self, pos_id):
        if pos_id in self:
            settings = self.session.settings
            position = self[pos_id]
            settings.set('imaging_zoom', position.zoom)
            settings.set('scan_voltage_multiplier', position.scan_voltage_multiplier)
            settings.set('scan_voltage_range_reference', position.scan_voltage_range_reference)
            settings.set('rotation', position.rotation)
            settings.set('fov_x', position.fov_xy[0])
            settings.set('fov_y', position.fov_xy[1])
            settings.set('zstep', position.zstep)


class Position:
    def __init__(self):
        self.coordinates = None
        self.ref_image = None
        self.ref_image_zoomed_out = None
        self.roi_x_y = None
        self.rotation = 0
        self.zoom = 10
        self.fov_xy = np.array([250, 250])
        self.scan_voltage_multiplier = np.array([1, 1])
        self.scan_voltage_range_reference = np.array([5, 5])
        self.zstep = 1

        self.drift_history = []

    def save(self):
        return dict(
            coordinates=self.coordinates.save(),
            ref_image=self.ref_image,
            roi_x_y=self.roi_x_y,
            drift_history=self.drift_history,
            zoom=self.zoom,
            fov_xy=self.fov_xy,
            scan_voltage_multiplier=self.scan_voltage_multiplier,
            scan_voltage_range_reference=self.scan_voltage_range_reference,
            zstep=self.zstep,
        )

    def load(self, loaded_position):
        self.coordinates.load(loaded_position['coordinates']),
        self.ref_image = loaded_position['ref_image']
        self.roi_x_y = loaded_position['roi_x_y']
        self.drift_history = loaded_position['drift_history']
        self.zoom = loaded_position['zoom']
        self.fov_xy = loaded_position('fov_xy')
        self.scan_voltage_multiplier = loaded_position('scan_voltage_multiplier')
        self.scan_voltage_range_reference = loaded_position('scan_voltage_range_reference')
        self.zstep = loaded_position('zstep')

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
