import os

import pickle

import numpy as np

from app.inherited.SpineTrackerSettings import SpineTrackerSettings
from guis.PositionsPage import PositionsPage


class PositionManagement(SpineTrackerSettings):

    def __init__(self, *args, **kwargs):
        super(PositionManagement, self).__init__(*args, **kwargs)
        self.positions = {}

    def initialize_positions(self):
        file_name = self.get_app_param('initDirectory') + 'positions.p'
        if os.path.isfile(file_name):
            self.positions = pickle.load(open(file_name, 'rb'))

    def get_current_position(self):
        if self.get_app_param('simulation'):
            # simulate position for now.
            # eventually, pull position from other program here
            x = np.random.randint(-100, 100)
            y = np.random.randint(-100, 100)
            z = np.random.randint(-100, 100)
        else:
            flag = 'currentPosition'
            self.getCommands.receivedFlags[flag] = False
            self.sendCommands.get_current_position()
            self.getCommands.wait_for_received_flag(flag)
            x, y, z = self.currentCoordinates
        return {'x': x, 'y': y, 'z': z}

    def create_new_pos(self, xyz, ref_images=None):
        # just starting with an empty dict for now
        if len(self.positions) == 0:
            pos_id = 1
        else:
            pos_id = max(self.positions.keys()) + 1
        self.positions[pos_id] = xyz
        if ref_images is None:
            # load sample ref images
            self.load_test_ref_image()
        else:
            self.acq['imgref_imaging'] = ref_images['imaging']
            self.acq['imgref_ref'] = ref_images['ref']
        self.positions[pos_id]['refImg'] = self.acq['imgref_imaging']
        self.positions[pos_id]['refImgZoomout'] = self.acq['imgref_ref']
        self.positions[pos_id]['xyzShift'] = np.array([0, 0, 0])
        roi_pos = np.array(self.positions[pos_id]['refImg'].shape) / 2
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
        xyz = self.get_current_position()
        self.positions[pos_id].update(xyz)
        self.frames[PositionsPage].redraw_position_table()
        self.backup_positions()

    def backup_positions(self):
        positions = self.positions
        pickle.dump(positions, open(self.get_app_param('initDirectory') + 'positions.p', 'wb'))
