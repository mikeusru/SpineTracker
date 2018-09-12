from queue import Queue
import os
from io_communication.CommandReader import CommandReader, ImagingParamFileHandler
from io_communication.CommandWriter import CommandWriter
from io_communication.file_listeners import FileReaderThread
import numpy as np


class Communication:

    def __init__(self, session):
        self.session = session
        self.settings = session.settings
        self.instructions_in_queue = Queue()
        self.command_writer = CommandWriter(self.session)
        self.command_reader = CommandReader(self.session, self.instructions_in_queue)
        #self.param_handler = ImagingParamFileHandler()
        self.instructions_listener_thread = self.initialize_instructions_listener_thread()
        #self.param_file_listener_thread = self.initialize_param_file_listener_thread()

    def initialize_instructions_listener_thread(self):
        input_file = self.settings.get('input_file')
        path, filename = os.path.split(input_file)
        read_function = self.command_reader.read_new_commands
        with self.instructions_in_queue.mutex:
            self.instructions_in_queue.queue.clear()
        instructions_listener_thread = FileReaderThread(self, path, filename, read_function)
        instructions_listener_thread.start()
        return instructions_listener_thread

    #def initialize_param_file_listener_thread(self):
    #    self.param_handler.init_session(self.session)
    #    self.param_handler.create_listener_thread()
    #    return self.param_handler.listener_thread

    def move_to_coordinates(self, coordinates):
        motor_x_y_z = coordinates.get_motor()
        scan_voltage_x_y = coordinates.get_scan_voltage_x_y()
        self.move_motor(motor_x_y_z['x'], motor_x_y_z['y'], motor_x_y_z['z'])
        self.set_scan_shift(scan_voltage_x_y['x'], scan_voltage_x_y['y'])

    def move_motor(self, x,y,z):
        response_command = 'stagemovedone'
        self.command_reader.set_response(response_command)
        self.command_writer.move_stage(x,y,z)
        self.command_reader.wait_for_response(response_command)

    def grab_stack(self):
        self.set_intensity_image_saving_on()
        response_command = 'acquisitiondone'
        self.command_reader.set_response(response_command)
        self.command_writer.grab_one_stack()
        self.command_reader.wait_for_response(response_command)

    def uncage(self, roi_x, roi_y):
        response_command = 'uncagingdone'
        self.command_reader.set_response(response_command)
        self.command_writer.do_uncaging(roi_x, roi_y)
        self.command_reader.wait_for_response(response_command)

    def set_scan_shift(self, scan_voltage_x, scan_voltage_y):
        response_command = 'scanvoltagexy'
        self.command_reader.set_response(response_command)
        self.command_writer.set_scan_shift(scan_voltage_x, scan_voltage_y)
        self.command_reader.wait_for_response(response_command)

    def set_z_slice_num(self, z_slice_num):
        response_command = 'zslicenum'
        self.command_reader.set_response(response_command)
        self.command_writer.set_z_slice_num(z_slice_num)
        self.command_reader.wait_for_response(response_command)

    def set_zoom(self, zoom):
        response_command = 'zoom'
        self.command_reader.set_response(response_command)
        self.command_writer.set_zoom(zoom)
        self.command_reader.wait_for_response(response_command)

    def set_resolution(self, x_resolution, y_resolution):
        response_command = 'resolutionxy'
        self.command_reader.set_response(response_command)
        self.command_writer.set_x_y_resolution(x_resolution, y_resolution)
        self.command_reader.wait_for_response(response_command)

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
        self.set_intensity_image_saving_on()  # Added by Ryohei
        self.command_reader.read_imaging_param_file() #Ryohei

    def set_reference_imaging_conditions(self):
        zoom = self.settings.get('reference_zoom')
        x_resolution = self.settings.get('normal_resolution_x')
        y_resolution = self.settings.get('normal_resolution_y')
        z_slice_num = self.settings.get('reference_slices')
        self.set_zoom(zoom)
        self.set_resolution(x_resolution, y_resolution)
        self.set_z_slice_num(z_slice_num)
        self.set_intensity_image_saving_on()   #Added by Ryohei
        self.command_reader.read_imaging_param_file()  #Ryohei

    def get_motor_position(self):
        response_command = 'currentposition'
        self.command_reader.set_response(response_command)
        self.command_writer.get_current_motor_position()
        self.command_reader.wait_for_response(response_command)

    def set_intensity_image_saving_on(self):
        if self.settings.get('intensity_saving') != 1:
            response_command = 'intensitysaving'
            self.command_reader.set_response(response_command)
            self.command_writer.set_intensity_saving(1)
            self.command_reader.wait_for_response(response_command)
