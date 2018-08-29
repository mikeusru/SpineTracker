import os


class CommandWriter:
    def __init__(self, settings):
        self.settings = settings
        self.file_path = settings.get('output_file')
        if not os.path.isfile(self.file_path):
            open(self.file_path, 'a').close()

    def move_stage(self, x, y, z):
        self.write_command('moveXYZ', x, y, z)

    def grab_one_stack(self):
        self.write_command('StartGrab')

    def set_zoom(self, zoom):
        self.write_command('setZoom', zoom)

    def do_uncaging(self, roi_x, roi_y):
        self.write_command('StartUncaging', roi_x, roi_y)

    def get_fov_size(self):
        self.write_command('GetFOVXY')

    def get_scan_voltage_xy(self):
        self.write_command('GetScanVoltageXY')

    def get_scan_voltage_multiplier(self):
        self.write_command('GetScanVoltageMultiplier')

    def get_scan_voltage_range_reference(self):
        self.write_command('GetScanVoltageRangeReference')

    def get_current_motor_position(self):
        self.write_command('getCurrentPosition')

    def set_scan_shift(self, scan_shift_fast, scan_shift_slow):
        self.write_command('setScanVoltageXY', scan_shift_fast, scan_shift_slow)

    def set_z_slice_num(self, z_slice_num):
        self.write_command('SetZSliceNum', z_slice_num)

    def set_x_y_resolution(self, x_resolution, y_resolution):
        self.write_command('SetResolutionXY', x_resolution, y_resolution)

    def get_x_y_resolution(self):
        self.write_command('GetResolutionXY')

    def write_command(self, *args):
        command = ",".join([str(x) for x in args])
        # self.controller.print_status('\nWriting Command {0}\n'.format(command))
        print('\nWriting Command {0}\n'.format(command))
        with open(self.file_path, "a") as f:
            f.write('\n' + command)
