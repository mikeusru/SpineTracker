import os

import pickle

import numpy as np

from app.main2 import ReferenceImage, ReferenceImageZoomedOut
from guis.PositionsPage import PositionsPage


class PositionsManager:

    def __init__(self, settings):
        self.settings = settings
        self.positions = Positions()

    def load_previous_positions(self):
        file_name = self.settings.get('init_directory') + 'positions.p'
        self.positions.load_positions_from_file(file_name)

    # def get_current_position(self):
    #     if self.settings.get('simulation'):
    #         # simulate position for now.
    #         # eventually, pull position from other program here
    #         x_with_scan_shift = np.random.randint(-100, 100)
    #         y_with_scan_shift = np.random.randint(-100, 100)
    #         z = np.random.randint(-100, 100)
    #     else:
    #         flag = 'current_positions'
    #         self.command_reader.received_flags[flag] = False
    #         self.command_writer.get_current_position()
    #         self.command_reader.wait_for_received_flag(flag)
    #         x, y, z = self.settings.get('current_motor_coordinates')
    #         flag = 'scan_angle_x_y'
    #         self.command_reader.received_flags[flag] = False
    #         self.command_writer.get_scan_angle_xy()
    #         self.command_reader.wait_for_received_flag(flag)
    #         current_scan_angle_x_y = self.settings.get('current_scan_angle_x_y')
    #         x_with_scan_shift, y_with_scan_shift = self.scan_angle_to_xy(current_scan_angle_x_y, x_center=x, y_center=y)
    #     return {'x': x_with_scan_shift, 'y': y_with_scan_shift, 'z': z}

    def get_roi_x_y(self, pos_id):
        roi_x, roi_y = self.positions[pos_id]['roi_position']
        return roi_x, roi_y

    def create_new_pos(self):
        xyz = self.settings.get('current_combined_coordinates')
        pos_id = self.positions.initialize_new_position()
        self.positions.set_coordinates(pos_id, xyz)
        self.positions[pos_id].set_ref_image()
        else:
            self.settings.set('imgref_imaging', ref_images['imaging'])
            self.settings.set('imgref_ref', ref_images['ref'])
        self.positions[pos_id]['ref_img'] = self.settings.get('imgref_imaging')
        self.positions[pos_id]['ref_img_zoomout'] = self.settings.get('imgref_ref')
        self.positions[pos_id]['xyzShift'] = np.array([0, 0, 0])
        roi_pos = np.array(self.positions[pos_id]['ref_img'].shape) / 2
        self.positions[pos_id]['roi_position'] = roi_pos

    def add_position(self, cont, xyz=None):
        if xyz is None:
            xyz = self.get_current_position()
        # add position to table
        self.create_new_pos(xyz)
        cont.redraw_position_table()
        self.backup_positions()

    def clear_positions(self, cont):
        self.positions = {}
        cont.redraw_position_table()

    def delete_positions(self, pos_id):
        del self.positions[pos_id]
        self.frames[PositionsPage].redraw_position_table()
        self.backup_positions()

    def update_position(self, pos_id):
        # TODO: Figure out what's going on here. maybe it's the motor controller, maybe not...
        xyz = self.get_current_position()
        self.positions[pos_id].update(xyz)
        self.frames[PositionsPage].redraw_position_table()
        self.backup_positions()

    def backup_positions(self):
        positions = self.positions
        pickle.dump(positions, open(self.settings.get('init_directory') + 'positions.p', 'wb'))


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
        self.ref_image_zoom_out = None
        self.roi_x_y = None

    def set_coordinates(self, xyz):
        self.coordinates.update(xyz)

    def set_ref_image(self, ref_image):
        self.ref_image = ref_image

    def set_ref_image_zoom_out(self, ref_image_zoom_out):
        self.ref_image_zoom_out = ref_image_zoom_out

    def set_roi_x_y(self, roi_x_y):
        self.roi_x_y = roi_x_y