from queue import Queue, Empty
from app.io_communication.CommandReader_pipe import CommandReader
from app.io_communication.CommandWriter_pipe import CommandWriter
from app.io_communication.Event import initialize_events
from app.io_communication.FLIM_pipeClient import FLIM_Com


class Communication:

    def __init__(self, session):
        self.session = session
        self.settings = session.settings
        self.events = initialize_events([
            'connection_made'
        ])
        self.instructions_in_queue = Queue()
        self.command_writer = None
        self.command_reader = None
        self.pipe_target = FLIM_Com()
        self.init_command_writer()
        self.init_command_reader()

    def init_command_reader(self):
        self.command_reader = CommandReader(self.instructions_in_queue)
        self.command_reader.stage_control_target += self.session.state.current_coordinates.set_motor
        self.command_reader.scan_voltage_target += self.session.state.current_coordinates.set_scan_voltages_x_y
        self.command_reader.setting_target += self.session.settings.set
        self.command_reader.logger += self.session.print_to_log
        self.command_reader.command_target += self.session.print_received_command
        self.command_reader.command_target += self.session.print_to_log
        self.command_reader.freeze_preventer += self.session.prevent_freezing_during_loops
        self.command_reader.fov_target += self.set_fov
        self.command_reader.create_read_settings()

    def init_command_writer(self):
        self.command_writer = CommandWriter()
        self.command_writer.command_target += self.session.print_sent_command
        self.command_writer.command_target += self.session.print_to_log
        self.command_writer.command_target += self.pipe_target.sendCommand

    def set_fov(self, x, y):
        self.settings.set('fov_x', x)
        self.settings.set('fov_y', y)

    def get_connection_status(self):
        return self.pipe_target.Connected

    def pipe_connect(self):
        # if connected and gui var is true, ignore
        if self.pipe_target.Connected and not self.settings.get_gui_var('pipe_connect_bool'):
            self.pipe_unsubscribe()
        elif not self.pipe_target.Connected and self.settings.get_gui_var('pipe_connect_bool'):
            self.pipe_target.messageReceived += self.pipe_client_message_received
            self.pipe_target.start()
            while not self.instructions_in_queue.empty():
                try:
                    self.instructions_in_queue.get(False)
                except Empty:
                    continue
            self.events['connection_made']()
        self.settings.set('pipe_connect_bool', self.pipe_target.Connected)

    def pipe_unsubscribe(self):
        self.pipe_target.messageReceived -= self.pipe_client_message_received
        if self.pipe_target.Connected:
            self.pipe_target.disconnect()

    def pipe_client_message_received(self, message, source):
        # if source == 'R':
        print('Message from FLIMage: {}'.format(message))
        # event-driven actions
        self.command_reader.read_new_command(message)
        # elif source == 'W' and self.pipe_target.debug:
        #     print('Mesage from FLIMage: {}'.format(message))
        #     simple reply
        self.settings.set('pipe_connect_bool', self.pipe_target.Connected)

    def move_to_coordinates(self, coordinates):
        motor_x_y_z = coordinates.get_motor()
        scan_voltage_x_y = coordinates.get_scan_voltage_x_y()
        self.move_motor(motor_x_y_z['x'], motor_x_y_z['y'], motor_x_y_z['z'])
        self.set_scan_shift(scan_voltage_x_y['x'], scan_voltage_x_y['y'])

    def move_motor(self, x, y, z):
        response_command = 'setmotorpositiondone'
        self.command_reader.set_response(response_command)
        self.command_writer.move_stage(x, y, z)
        self.command_reader.wait_for_response(response_command)
        pass

    def grab_stack(self):
        self.set_intensity_image_saving_on()
        response_command = 'acquisitiondone'
        self.command_reader.set_response(response_command)
        self.command_writer.grab_one_stack()
        self.command_reader.wait_for_response(response_command)
        self.get_intensity_file_path()

    def get_intensity_file_path(self):
        response_command = 'intensityfilepath'
        self.command_reader.set_response(response_command)
        self.command_writer.get_intensity_file_path()
        self.command_reader.wait_for_response(response_command)

    def toggle_uncaging(self, uncaging_toggle):
        response_command = 'uncaging processed.'
        self.command_reader.set_response(response_command)
        uncaging_toggle = int(uncaging_toggle)
        self.command_writer.toggle_uncaging(uncaging_toggle)
        self.command_reader.wait_for_response(response_command)

    def uncage(self, roi_x, roi_y):
        response_command = 'uncagingdone'
        self.command_reader.set_response(response_command)
        self.command_writer.do_uncaging(roi_x, roi_y)
        self.command_reader.wait_for_response(response_command)

    def set_uncaging_location(self, roi_x, roi_y):
        response_command = 'uncaginglocation'
        self.command_reader.set_response(response_command)
        self.command_writer.set_uncaging_location(roi_x, roi_y)
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

    def set_reference_imaging_conditions(self):
        zoom = self.settings.get('reference_zoom')
        x_resolution = self.settings.get('normal_resolution_x')
        y_resolution = self.settings.get('normal_resolution_y')
        z_slice_num = self.settings.get('reference_slices')
        self.set_zoom(zoom)
        self.set_resolution(x_resolution, y_resolution)
        self.set_z_slice_num(z_slice_num)
        self.set_intensity_image_saving_on()  # Added by Ryohei

    def send_custom_command(self, custom_command):
        if custom_command != '':
            response_command = 'customcommandreceived'
            self.command_reader.set_response(response_command)
            self.command_writer.write_custom_command(custom_command)
            self.command_reader.wait_for_response(response_command)

    def set_imaging_settings_file(self, imaging_settings_file):
        if imaging_settings_file != '':
            response_command = 'setting'
            self.command_reader.set_response(response_command)
            self.command_writer.set_imaging_settings_file(imaging_settings_file)
            self.command_reader.wait_for_response(response_command)

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

    def get_imaging_settings(self):
        self.get_scan_voltage_range_reference()
        self.get_scan_voltage_multiplier()

    def get_scan_voltage_range_reference(self):
        response_command = 'scanvoltagerangereference'
        self.command_reader.set_response(response_command)
        self.command_writer.get_scan_voltage_range_reference()
        self.command_reader.wait_for_response(response_command)

    def get_scan_voltage_multiplier(self):
        response_command = 'scanvoltagemultiplier'
        self.command_reader.set_response(response_command)
        self.command_writer.get_scan_voltage_multiplier()
        self.command_reader.wait_for_response(response_command)
