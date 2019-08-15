import os


class CommandWriter:
    def __init__(self, session):
        self.session = session
        self.settings = session.settings
        self.file_path = self.settings.get('output_file')
        if not os.path.isfile(self.file_path):
            open(self.file_path, 'a').close()

    def move_stage(self, x, y, z):
        self.write_command('SetMotorPosition', x, y, z)

    def grab_one_stack(self):
        self.write_command('StartGrab')

    def set_zoom(self, zoom):
        self.write_command('SetZoom', zoom)

    def set_intensity_saving(self, save_intensity_image_1_or_0):
        self.write_command('SetIntensitySaving', save_intensity_image_1_or_0)

    def do_uncaging(self, roi_x, roi_y):
        self.write_command('StartUncaging', roi_x, roi_y)

    def get_scan_voltage_xy(self):
        self.write_command('GetScanVoltageXY')

    def get_scan_voltage_multiplier(self):
        self.write_command('GetScanVoltageMultiplier')

    def get_scan_voltage_range_reference(self):
        self.write_command('GetScanVoltageRangeReference')

    def get_current_motor_position(self):
        self.write_command('GetCurrentPosition')

    def set_scan_shift(self, scan_shift_fast, scan_shift_slow):
        self.write_command('SetScanVoltageXY', scan_shift_fast, scan_shift_slow)

    def set_z_slice_num(self, z_slice_num):
        self.write_command('SetZSliceNum', z_slice_num)

    def set_x_y_resolution(self, x_resolution, y_resolution):
        self.write_command('SetResolutionXY', x_resolution, y_resolution)

    def load_setting_file(self, file_number):
        self.write_command('LoadSetting', file_number)

    def set_uncaging_location(self, x_pixel, y_pixel):
        self.write_command('SetUncagingLocation', x_pixel, y_pixel)

    def write_custom_command(self, custom_command):
        self.write_command('CustomCommand', custom_command)

    def write_command(self, *args):
        command = ",".join([str(x) for x in args])
        self.print_line('\nWriting Command {0}\n'.format(command))
        self.session.communication.pipe_target.sendCommand(command)

    def print_line(self, line):
        self.session.print_sent_command(line)
        self.session.print_to_log(line)
