import numpy as np


class Coordinates:
    def __init__(self):
        self.motor_x = 0
        self.motor_y = 0
        self.motor_z = 0
        self.scan_voltage_x = 0
        self.scan_voltage_y = 0
        self.settings_reader = None
        self.center_motor_reader = None
        self.scan_voltage_range_reference = None
        self.fov_x_y = None
        self.xy_inverter = {
            'motor_x': 1,
            'motor_y': 1,
            'scan_shift_x': 1,
            'scan_shift_y': 1,
        }

    def save(self):
        return dict(
            motor_x=self.motor_x,
            motor_y=self.motor_y,
            motor_z=self.motor_z,
            scan_voltage_x=self.scan_voltage_x,
            scan_voltage_y=self.scan_voltage_y,
        )

    def load(self, coordinates):
        self.motor_x = coordinates['motor_x']
        self.motor_y = coordinates['motor_y']
        self.motor_z = coordinates['motor_z']
        self.scan_voltage_x = coordinates['scan_voltage_x']
        self.scan_voltage_y = coordinates['scan_voltage_y']

    def set_motor(self, x=None, y=None, z=None):
        if x is not None:
            self.motor_x = float(x)
        if y is not None:
            self.motor_y = float(y)
        if z is not None:
            self.motor_z = float(z)

    def copy(self):
        new_coordinates = Coordinates()
        new_coordinates.motor_x = self.motor_x
        new_coordinates.motor_y = self.motor_y
        new_coordinates.motor_z = self.motor_z
        new_coordinates.scan_voltage_x = self.scan_voltage_x
        new_coordinates.scan_voltage_y = self.scan_voltage_y
        new_coordinates.settings_reader = self.settings_reader
        new_coordinates.center_motor_reader = self.center_motor_reader
        return new_coordinates

    def update_to_drift(self, drift_x_y_z):
        xyz_old = self.get_combined()
        x_old, y_old, z_old = [xyz_old[xyz] for xyz in ['x', 'y', 'z']]
        x_drift = drift_x_y_z.x_um
        y_drift = drift_x_y_z.y_um
        z_drift = drift_x_y_z.z_um
        x_new = x_old + x_drift
        y_new = y_old + y_drift
        z_new = z_old + z_drift
        self.set_combined_coordinates(x_new, y_new, z_new)

    def set_combined_coordinates(self, x, y, z):
        scan_voltage_x, scan_voltage_y = self.x_y_to_scan_voltage(x, y)
        self.set_scan_voltages_x_y(scan_voltage_x, scan_voltage_y)
        self.set_motor(z=z)

    def set_relative_to_center_coordinates(self, x, y, z):  # Ryohei.
        self.set_scan_voltages_x_y(0, 0)
        self.set_motor(x=x, y=y, z=z)

    def set_scan_voltages_x_y(self, x=None, y=None):
        if x is not None:
            self.scan_voltage_x = float(x)
        if y is not None:
            self.scan_voltage_y = float(y)

    def get_motor(self):
        return dict(x=self.motor_x, y=self.motor_y, z=self.motor_z)

    def get_scan_voltage_x_y(self):
        return dict(x=self.scan_voltage_x, y=self.scan_voltage_y)

    def get_combined(self):
        scan_x_y = self.scan_voltage_to_um()
        x_combined, y_combined = scan_x_y + np.array([self.motor_x, self.motor_y])
        return dict(x=x_combined, y=y_combined, z=self.motor_z)

    def scan_voltage_to_um(self):
        self.update_values_from_settings()
        scan_voltage_x = self.scan_voltage_x * self.xy_inverter['scan_shift_x']
        scan_voltage_y = self.scan_voltage_y * self.xy_inverter['scan_shift_y']
        fs_angular = np.array([scan_voltage_x, scan_voltage_y])
        fs_normalized = fs_angular / self.scan_voltage_range_reference
        fs_coordinates = fs_normalized * self.fov_x_y
        return fs_coordinates

    def x_y_to_scan_voltage(self, x, y):
        self.update_values_from_settings()
        # convert x and y to relative pixel coordinates
        fs_coordinates = np.array([x - self.motor_x, y - self.motor_y])
        fs_normalized = fs_coordinates / self.fov_x_y
        fs_angular = fs_normalized * self.scan_voltage_range_reference
        scan_voltage_x, scan_voltage_y = fs_angular
        scan_voltage_x *= self.xy_inverter['scan_shift_x']
        scan_voltage_y *= self.xy_inverter['scan_shift_y']
        return scan_voltage_x, scan_voltage_y

    def update_to_center(self):
        center_xyz = self.center_motor_reader()
        x_motor, y_motor = center_xyz['x'], center_xyz['y']
        old_xyz = self.get_combined()
        old_x = old_xyz['x']
        old_y = old_xyz['y']
        self.set_motor(x=x_motor, y=y_motor)
        scan_voltage_x, scan_voltage_y = self.x_y_to_scan_voltage(old_x, old_y)
        self.set_scan_voltages_x_y(scan_voltage_x, scan_voltage_y)

    def update_values_from_settings(self):
        self.scan_voltage_range_reference = np.array(self.settings_reader('scan_voltage_range_reference'))
        self.fov_x_y = np.squeeze(np.array([self.settings_reader('fov_x'), self.settings_reader('fov_y')]))
        self.xy_inverter = {
            'motor_x': 1 - 2 * self.settings_reader('invert_motor_x'),
            'motor_y': 1 - 2 * self.settings_reader('invert_motor_y'),
            'scan_shift_x': 1 - 2 * self.settings_reader('invert_scan_shift_x'),
            'scan_shift_y': 1 - 2 * self.settings_reader('invert_scan_shift_y'),
        }
        if self.settings_reader('invert_scan_shift_x'):
            self.xy_inverter['scan_shift_x'] = -1
        else:
            self.xy_inverter['scan_shift_x'] = 1
