import os


class SendCommands(object):
    def __init__(self, controller, file_path, *args, **kwargs):
        self.controller = controller
        self.file_path = file_path
        self.args = args
        self.kwargs = kwargs
        if not os.path.isfile(file_path):
            open(file_path, 'a').close()

    def move_stage(self, x, y, z):
        self.write_command('moveXYZ', x, y, z)

    def grab_one_stack(self):
        self.write_command('grabOneStack')

    def set_zoom(self, zoom):
        self.write_command('setZoom', zoom)

    def do_uncaging(self, roi_x, roi_y):
        self.write_command('runUncaging', roi_x, roi_y)

    def get_fov_size(self):
        self.write_command('getFOV_xy')

    def get_scan_angle_xy(self):
        self.write_command('getScanAngleXY')

    def get_scan_angle_multiplier(self):
        self.write_command('getScanAngleMultiplier')

    def get_scan_angle_range_reference(self):
        self.write_command('getScanAngleRangeReference')

    def get_current_position(self):
        self.write_command('getCurrentPosition', 'xyz')

    def set_scan_shift(self, scan_shift_fast, scan_shift_slow):
        self.write_command('setScanAngleXY', scan_shift_fast, scan_shift_slow)

    def set_z_slice_num(self, z_slice_num):
        self.write_command('setZSliceNum', z_slice_num)

    def set_x_y_resolution(self, x_resolution, y_resolution):
        self.write_command('setXYResolution', x_resolution, y_resolution)

    def get_x_y_resolution(self):
        self.write_command('getXYResolution')

    def write_command(self, *args):
        command = ",".join([str(x) for x in args])
        self.controller.print_status('\nWriting Command {0}\n'.format(command))
        with open(self.file_path, "a") as f:
            f.write('\n' + command)
