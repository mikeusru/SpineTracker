import os

import pickle

import numpy as np

from app.Position import Position


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
            xyz = coordinates.get_combined()
            x_list.append(xyz['x'])
            y_list.append(xyz['y'])
            z_list.append(xyz['z'])
        x_average = np.average(np.array(x_list))
        y_average = np.average(np.array(y_list))
        z_average = np.average(np.array(z_list))
        return dict(x=x_average, y=y_average, z=z_average)

    def update_all_coordinates_relative_to_center(self):
        for pos_id in self:
            self[pos_id].coordinates.update_to_center()

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
            positions_dict.update({key: val.save()})
        pickle.dump(positions_dict, open(self.settings.get('init_directory') + 'positions.p', 'wb'))

    def record_drift_history_of_acquired_image(self, acquired_image):
        pos_id = acquired_image.pos_id
        drift_x_y_z = acquired_image.drift_x_y_z.copy()
        self[pos_id].record_drift_history(drift_x_y_z)

    def load_previous_positions(self, center_coordinates):
        file_name = self.settings.get('init_directory') + 'positions.p'
        try:
            if os.path.isfile(file_name):
                positions_dict = pickle.load(open(file_name, 'rb'))
                pos_id = 1
                for pos_id, position_dict in positions_dict.items():
                    self[pos_id] = Position()
                    self[pos_id].load(position_dict, center_coordinates)
                self.current_position = pos_id
        except EOFError as err:
            print('Error loading positions: {}'.format(err))

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

    def clear_file_record(self):
        for pos_id in self:
            self[pos_id].clear_file_names()

    def rename_latest_files(self, pos_id):
        self[pos_id].rename_file(pos_id)


