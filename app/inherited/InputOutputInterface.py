import numpy as np

from app.inherited.inherited.PositionManagement import PositionManagement
from io_communication.GetCommands import GetCommands
from io_communication.SendCommands import SendCommands


class InputOutputInterface(PositionManagement):

    def __init__(self, *args, **kwargs):
        super(InputOutputInterface, self).__init__(*args, **kwargs)
        self.outputFile = "../instructions_output.txt"
        self.inputFile = "../instructions_input.txt"
        self.instructions = []
        self.sendCommands = SendCommands(self, self.outputFile)
        self.getCommands = GetCommands(self, self.inputFile)

    def move_stage(self, x=None, y=None, z=None, pos_id=None):
        if pos_id is not None:
            x, y, z = [self.positions[pos_id][key] for key in ['x', 'y', 'z']]
        if self.get_settings('park_xy_motor'):
            x_motor, y_motor = self.acq['center_xy']
            self.set_scan_shift(x, y)
        else:
            x_motor = x
            y_motor = y
        flag = 'stageMoveDone'
        self.getCommands.receivedFlags[flag] = False
        self.sendCommands.move_stage(x_motor, y_motor, z)
        self.getCommands.wait_for_received_flag(flag)

    def grab_stack(self):
        flag = 'grabOneStackDone'
        self.getCommands.receivedFlags[flag] = False
        self.sendCommands.grab_one_stack()
        self.getCommands.wait_for_received_flag(flag)

    def uncage(self, roi_x, roi_y):
        flag = 'uncagingDone'
        self.getCommands.receivedFlags[flag] = False
        self.sendCommands.do_uncaging(roi_x, roi_y)
        self.getCommands.wait_for_received_flag(flag)

    def set_scan_shift(self, x, y):
        scan_shift_fast, scan_shift_slow = self.xy_to_scan_angle(x, y)
        flag = 'scanAngleXY'
        self.getCommands.receivedFlags[flag] = False
        self.sendCommands.set_scan_shift(scan_shift_fast, scan_shift_slow)
        self.getCommands.wait_for_received_flag(flag)

    def set_z_slice_num(self, z_slice_num):
        flag = 'z_slice_num'
        self.getCommands.receivedFlags[flag] = False
        self.sendCommands.set_z_slice_num(z_slice_num)
        self.getCommands.wait_for_received_flag(flag)

    def xy_to_scan_angle(self, x, y):
        scan_angle_multiplier = np.array(self.scanAngleMultiplier)
        scan_angle_range_reference = np.array(self.scanAngleRangeReference)
        fov = np.array(self.settings['fov_x_y'])
        # convert x and y to relative pixel coordinates
        x_center, y_center = self.acq['center_xy']
        xc = x - x_center
        yc = y - y_center
        fs_coordinates = np.array([xc, yc])
        scan_shift = np.array([0, 0])
        fs_normalized = fs_coordinates / fov
        fs_angular = scan_shift + fs_normalized * scan_angle_multiplier * scan_angle_range_reference
        scan_shift_fast, scan_shift_slow = fs_angular
        return scan_shift_fast, scan_shift_slow

    def get_scan_props(self):
        flag = 'scanAngleMultiplier'
        self.getCommands.receivedFlags[flag] = False
        self.sendCommands.get_scan_angle_multiplier()
        self.getCommands.wait_for_received_flag(flag)

        flag = 'scanAngleRangeReference'
        self.getCommands.receivedFlags[flag] = False
        self.sendCommands.get_scan_angle_range_reference()
        self.getCommands.wait_for_received_flag(flag)

    def set_zoom(self, zoom):
        flag = 'zoom'
        self.getCommands.receivedFlags[flag] = False
        self.sendCommands.set_zoom(zoom)
        self.getCommands.wait_for_received_flag(flag)

    def set_resolution(self, x_resolution, y_resolution):
        flag = 'x_y_resolution'
        self.getCommands.receivedFlags[flag] = False
        self.sendCommands.set_x_y_resolution(x_resolution, y_resolution)
        self.getCommands.wait_for_received_flag(flag)

    def set_macro_imaging_conditions(self):
        zoom = self.get_settings('macro_zoom')
        x_resolution = self.get_settings('macro_resolution_x')
        y_resolution = self.get_settings('macro_resolution_y')
        z_slice_num = self.get_settings('macro_z_slices')
        self.set_zoom(zoom)
        self.set_resolution(x_resolution, y_resolution)
        self.set_z_slice_num(z_slice_num)

    def set_normal_imaging_conditions(self):
        zoom = self.get_settings('imaging_zoom')
        x_resolution = self.get_settings('normal_resolution_x')
        y_resolution = self.get_settings('normal_resolution_y')
        z_slice_num = self.get_settings('imaging_slices')
        self.set_zoom(zoom)
        self.set_resolution(x_resolution, y_resolution)
        self.set_z_slice_num(z_slice_num)


    def set_reference_imaging_conditions(self):
        zoom = self.get_settings('reference_zoom')
        x_resolution = self.get_settings('normal_resolution_x')
        y_resolution = self.get_settings('normal_resolution_y')
        z_slice_num = self.get_settings('reference_slices')
        self.set_zoom(zoom)
        self.set_resolution(x_resolution, y_resolution)
        self.set_z_slice_num(z_slice_num)
