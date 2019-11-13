from io_communication.CommandHandler import CommandHandler


class CommandWriter(CommandHandler):
    def __init__(self):
        super().__init__()
        self.print_function = None

    def move_stage(self, x, y, z):
        self.handle_command('SetMotorPosition', x, y, z)

    def grab_one_stack(self):
        self.handle_command('StartGrab')

    def set_zoom(self, zoom):
        self.handle_command('SetZoom', zoom)

    def set_intensity_saving(self, save_intensity_image_1_or_0):
        self.handle_command('SetIntensitySaving', save_intensity_image_1_or_0)

    def do_uncaging(self, roi_x, roi_y):
        self.handle_command('StartUncaging', roi_x, roi_y)

    def get_scan_voltage_xy(self):
        self.handle_command('GetScanVoltageXY')

    def get_scan_voltage_multiplier(self):
        self.handle_command('GetScanVoltageMultiplier')

    def get_scan_voltage_range_reference(self):
        self.handle_command('GetScanVoltageRangeReference')

    def get_current_motor_position(self):
        self.handle_command('GetCurrentPosition')

    def set_scan_shift(self, scan_shift_fast, scan_shift_slow):
        self.handle_command('SetScanVoltageXY', scan_shift_fast, scan_shift_slow)

    def set_z_slice_num(self, z_slice_num):
        self.handle_command('SetZSliceNum', z_slice_num)

    def set_x_y_resolution(self, x_resolution, y_resolution):
        self.handle_command('SetResolutionXY', x_resolution, y_resolution)

    def load_setting_file(self, file_number):
        self.handle_command('LoadSetting', file_number)

    def set_uncaging_location(self, x_pixel, y_pixel):
        self.handle_command('SetUncagingLocation', x_pixel, y_pixel)

    def write_custom_command(self, custom_command):
        self.handle_command('CustomCommand', custom_command)

    def handle_command(self, *args):
        command = ",".join([str(x) for x in args])
        self.write_command(command)

    def write_command(self, command):
        self.command_target(command)
