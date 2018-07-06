import numpy as np


class Coordinates:
    def __init__(self, settings):
        self.settings = settings
        self.motor_x = 0
        self.motor_y = 0
        self.motor_z = 0
        self.scan_angle_x = 0
        self.scan_angle_y = 0

    def set_motor(self, x=None, y=None, z=None):
        if x is not None:
            self.motor_x = float(x)
        if y is not None:
            self.motor_y = float(y)
        if z is not None:
            self.motor_z = float(z)

    def set_scan_angles_x_y(self, x=None, y=None):
        if x is not None:
            self.scan_angle_x = float(x)
        if y is not None:
            self.scan_angle_y = float(y)

    def get_motor(self):
        return dict(x=self.motor_x, y=self.motor_y, z=self.motor_z)

    def get_scan_angle_x_y(self):
        return dict(x=self.scan_angle_x, y=self.scan_angle_y)

    def get_combined(self):
        scan_x_y = self.scan_angle_to_um()
        x_combined, y_combined = scan_x_y + np.array([self.motor_x, self.motor_y])
        return dict(x=x_combined, y=y_combined, z=self.motor_z)

    def scan_angle_to_um(self):
        scan_angle_multiplier = self.settings.get('scan_angle_multiplier')
        scan_angle_range_reference = self.settings.get('scan_angle_range_reference')
        fov_x_y = np.squeeze(np.array([self.settings.get('fov_x'),self.settings.get('fov_y')]))
        fs_angular = np.array([self.scan_angle_x, -self.scan_angle_y])
        fs_normalized = fs_angular / (scan_angle_multiplier * scan_angle_range_reference)
        fs_coordinates = fs_normalized * fov_x_y
        return fs_coordinates