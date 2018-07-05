from queue import Queue
import os
from io_communication.CommandReader import CommandReader
from io_communication.CommandWriter import CommandWriter
from io_communication.file_listeners import InstructionThread
import numpy as np


class Communication:

    def __init__(self, session):
        self.session = session
        self.settings = session.settings
        self.instructions_received = []
        self.instructions_in_queue = Queue()
        self.command_writer = CommandWriter(self.settings)
        self.command_reader = CommandReader(self.session, self.instructions_in_queue, self.instructions_received)
        self.instructions_listener_thread = self.initialize_instructions_listener_thread()

    def initialize_instructions_listener_thread(self):
        input_file = self.settings.get('input_file')
        path, filename = os.path.split(input_file)
        read_function = self.command_reader.read_new_commands
        with self.instructions_in_queue.mutex:
            self.instructions_in_queue.queue.clear()
            instructions_listener_thread = InstructionThread(self, path, filename, read_function)
            instructions_listener_thread.start()
        return instructions_listener_thread

    def move_stage(self, x=None, y=None, z=None):
        if self.settings.get('park_xy_motor'):
            x_motor, y_motor, _ = self.session.state.center_coordinates.get_motor_coordinates()
            self.set_scan_shift(x, y)
        else:
            x_motor = x
            y_motor = y
        flag = 'stage_move_done'
        self.command_reader.received_flags[flag] = False
        self.command_writer.move_stage(x_motor, y_motor, z)
        self.command_reader.wait_for_received_flag(flag)

    def grab_stack(self):
        flag = 'grab_one_stack_done'
        self.command_reader.received_flags[flag] = False
        self.command_writer.grab_one_stack()
        self.command_reader.wait_for_received_flag(flag)

    def uncage(self, roi_x, roi_y):
        flag = 'uncaging_done'
        self.command_reader.received_flags[flag] = False
        self.command_writer.do_uncaging(roi_x, roi_y)
        self.command_reader.wait_for_received_flag(flag)

    def set_scan_shift(self, x, y):
        scan_shift_fast, scan_shift_slow = self.xy_to_scan_angle(x, y)
        flag = 'scan_angle_x_y'
        self.command_reader.received_flags[flag] = False
        self.command_writer.set_scan_shift(scan_shift_fast, scan_shift_slow)
        self.command_reader.wait_for_received_flag(flag)

    def set_z_slice_num(self, z_slice_num):
        flag = 'z_slice_num'
        self.command_reader.received_flags[flag] = False
        self.command_writer.set_z_slice_num(z_slice_num)
        self.command_reader.wait_for_received_flag(flag)

    def xy_to_scan_angle(self, x, y):
        scan_angle_multiplier = np.array(self.settings.get('scan_angle_multiplier'))
        scan_angle_range_reference = np.array(self.settings.get('scan_angle_range_reference'))
        fov = np.array(self.settings.get('fov_x_y'))
        # convert x and y to relative pixel coordinates
        x_center, y_center, _ = self.session.state.center_coordinates.get_motor_coordinates()
        fs_coordinates = np.array([x - x_center, y - y_center])
        fs_normalized = fs_coordinates / fov
        fs_angular = fs_normalized * scan_angle_multiplier * scan_angle_range_reference
        scan_shift_fast, scan_shift_slow = fs_angular
        # TODO: Add setting to invert scan shift. Or just tune it automatically.
        return scan_shift_fast, -scan_shift_slow

    def scan_angle_to_xy(self, scan_angle_x_y, x_center=None, y_center=None):
        scan_angle_multiplier = np.array(self.settings.get('scan_angle_multiplier'))
        scan_angle_range_reference = np.array(self.settings.get('scan_angle_range_reference'))
        fov = np.array(self.settings.get('fov_x_y'))
        fs_angular = np.array([scan_angle_x_y[0], -scan_angle_x_y[1]])
        if x_center is None:
            x_center, y_center, _ = self.session.state.center_coordinates.get_motor_coordinates()
        fs_normalized = fs_angular / (scan_angle_multiplier * scan_angle_range_reference)
        fs_coordinates = fs_normalized * fov
        x, y = fs_coordinates + np.array([x_center, y_center])
        return x, y

    def get_scan_props(self):
        flag = 'scanAngleMultiplier'
        self.command_reader.received_flags[flag] = False
        self.command_writer.get_scan_angle_multiplier()
        self.command_reader.wait_for_received_flag(flag)

        flag = 'scanAngleRangeReference'
        self.command_reader.received_flags[flag] = False
        self.command_writer.get_scan_angle_range_reference()
        self.command_reader.wait_for_received_flag(flag)

    def set_zoom(self, zoom):
        flag = 'zoom'
        self.command_reader.received_flags[flag] = False
        self.command_writer.set_zoom(zoom)
        self.command_reader.wait_for_received_flag(flag)
        self.settings.set('current_zoom', zoom)

    def set_resolution(self, x_resolution, y_resolution):
        flag = 'x_y_resolution'
        self.command_reader.received_flags[flag] = False
        self.command_writer.set_x_y_resolution(x_resolution, y_resolution)
        self.command_reader.wait_for_received_flag(flag)

    def set_macro_imaging_conditions(self):
        zoom = self.settings.get('macro_zoom')
        x_resolution = self.settings.get('macro_resolution_x')
        y_resolution = self.settings.get('macro_resolution_y')
        z_slice_num = self.settings.get('macro_z_slices')
        self.set_zoom(zoom)
        self.set_resolution(x_resolution, y_resolution)
        self.set_z_slice_num(z_slice_num)

    def set_normal_imaging_conditions(self):
        zoom = self.settings.get('imaging_zoom')
        x_resolution = self.settings.get('normal_resolution_x')
        y_resolution = self.settings.get('normal_resolution_y')
        z_slice_num = self.settings.get('imaging_slices')
        self.set_zoom(zoom)
        self.set_resolution(x_resolution, y_resolution)
        self.set_z_slice_num(z_slice_num)

    def set_reference_imaging_conditions(self):
        zoom = self.settings.get('reference_zoom')
        x_resolution = self.settings.get('normal_resolution_x')
        y_resolution = self.settings.get('normal_resolution_y')
        z_slice_num = self.settings.get('reference_slices')
        self.set_zoom(zoom)
        self.set_resolution(x_resolution, y_resolution)
        self.set_z_slice_num(z_slice_num)

    def get_current_position(self):
        flag = 'current_positions'
        self.command_reader.received_flags[flag] = False
        self.command_writer.get_current_motor_position()
        self.command_reader.wait_for_received_flag(flag)
        flag = 'scan_angle_x_y'
        self.command_reader.received_flags[flag] = False
        self.command_writer.get_scan_angle_xy()
        self.command_reader.wait_for_received_flag(flag)
