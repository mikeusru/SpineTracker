import os

import pickle

import numpy as np

from app.inherited.inherited.inherited.SpineTrackerSettings import Initializer
from guis.PositionsPage import PositionsPage


class PositionManagement(Initializer):

    def __init__(self, *args, **kwargs):
        super(PositionManagement, self).__init__(*args, **kwargs)
        self.positions = {}

    def initialize_positions(self):
        file_name = self.settings.get('init_directory') + 'positions.p'
        if os.path.isfile(file_name):
            self.positions = pickle.load(open(file_name, 'rb'))

    def get_current_position(self):
        if self.settings.get('simulation'):
            # simulate position for now.
            # eventually, pull position from other program here
            x_with_scan_shift = np.random.randint(-100, 100)
            y_with_scan_shift = np.random.randint(-100, 100)
            z = np.random.randint(-100, 100)
        else:
            flag = 'currentPosition'
            self.command_reader.received_flags[flag] = False
            self.command_writer.get_current_position()
            self.command_reader.wait_for_received_flag(flag)
            x, y, z = self.settings.get('current_coordinates')
            flag = 'scanAngleXY'
            self.command_reader.received_flags[flag] = False
            self.command_writer.get_scan_angle_xy()
            self.command_reader.wait_for_received_flag(flag)
            current_scan_angle_x_y = self.settings.get('current_scan_angle_x_y')
            x_with_scan_shift, y_with_scan_shift = self.scan_angle_to_xy(current_scan_angle_x_y, x_center=x, y_center=y)
        return {'x': x_with_scan_shift, 'y': y_with_scan_shift, 'z': z}

    def create_new_pos(self, xyz, ref_images=None):
        # just starting with an empty dict for now
        if len(self.positions) == 0:
            pos_id = 1
        else:
            pos_id = max(self.positions.keys()) + 1
        self.positions[pos_id] = xyz
        if ref_images is None:
            # load sample ref images
            if self.settings.get('simulation'):
                self.load_test_ref_image()
            else:
                self.grab_stack()
                self.load_acquired_image()
                # TODO: Set to acquire zoomed out image first
                self.settings.set('imgref_imaging', np.max(self.settings.get('image_stack').copy(), axis=0))
                self.settings.set('imgref_ref', np.max(self.settings.get('image_stack').copy(), axis=0))
        else:
            self.settings.set('imgref_imaging', ref_images['imaging'])
            self.settings.set('imgref_ref', ref_images['ref'])
        self.positions[pos_id]['ref_img'] = self.settings.get('imgref_imaging')
        self.positions[pos_id]['ref_img_zoomout'] = self.settings.get('imgref_ref')
        self.positions[pos_id]['xyzShift'] = np.array([0, 0, 0])
        roi_pos = np.array(self.positions[pos_id]['ref_img'].shape) / 2
        self.positions[pos_id]['roi_position'] = roi_pos

    def add_position(self, cont, xyz=None, ref_images=None):
        if xyz is None:
            xyz = self.get_current_position()
        # add position to table
        self.create_new_pos(xyz, ref_images=ref_images)
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
