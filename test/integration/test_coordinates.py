from unittest.mock import MagicMock

import pytest

from app.Coordinates import Coordinates


@pytest.fixture()
def coordinates():
    coordinates = Coordinates()
    coordinates.settings_reader_dict = {
        'scan_voltage_range_reference': [15, 15],
        'fov_x': 250,
        'fov_y': 250,
        'invert_motor_x': False,
        'invert_motor_y': False,
        'invert_scan_shift_x': False,
        'invert_scan_shift_y': False,
        'park_xy_motor': True
    }
    coordinates.settings_reader = coordinates.settings_reader_dict.get
    return coordinates


def test_x_y_to_scan_voltage(coordinates):
    scan_x, scan_y = coordinates.x_y_to_scan_voltage(100, 150)
    assert coordinates.xy_inverter['scan_shift_x'] == 1
    assert scan_x == 6
    assert scan_y == 9


def test_x_y_to_scan_voltage_inverse_x(coordinates):
    coordinates.settings_reader_dict['invert_scan_shift_x'] = True
    scan_x, scan_y = coordinates.x_y_to_scan_voltage(100, 150)
    assert coordinates.xy_inverter['scan_shift_x'] == -1
    assert scan_x == -6
    assert scan_y == 9


def test_x_y_to_scan_voltage_inverse_y(coordinates):
    coordinates.settings_reader_dict['invert_scan_shift_y'] = True
    scan_x, scan_y = coordinates.x_y_to_scan_voltage(100, 150)
    assert coordinates.xy_inverter['scan_shift_y'] == -1
    assert scan_x == 6
    assert scan_y == -9


def test_update_values_from_settings(coordinates):
    coordinates.settings_reader_dict['invert_scan_shift_x'] = True
    coordinates.update_values_from_settings()
    assert coordinates.settings_reader_dict['invert_scan_shift_x'] == True
    assert coordinates.xy_inverter['scan_shift_x'] == -1


def test_scan_voltage_to_um(coordinates):
    coordinates.scan_voltage_x = 6
    coordinates.scan_voltage_y = 9
    fs_coordinates = coordinates.scan_voltage_to_um()
    assert fs_coordinates[0] == 100
    assert fs_coordinates[1] == 150


def test_scan_voltage_to_um_inverted_x(coordinates):
    coordinates.scan_voltage_x = -6
    coordinates.scan_voltage_y = 9
    coordinates.settings_reader_dict['invert_scan_shift_x'] = True
    fs_coordinates = coordinates.scan_voltage_to_um()
    assert fs_coordinates[0] == 100
    assert fs_coordinates[1] == 150


def test_scan_voltage_to_um_inverted_y(coordinates):
    coordinates.scan_voltage_x = 6
    coordinates.scan_voltage_y = -9
    coordinates.settings_reader_dict['invert_scan_shift_y'] = True
    fs_coordinates = coordinates.scan_voltage_to_um()
    assert fs_coordinates[0] == 100
    assert fs_coordinates[1] == 150


def test_set_combined_coordinates(coordinates):
    x, y, z = (100, 150, 30)
    coordinates.set_combined_coordinates(x, y, z)
    assert coordinates.scan_voltage_x == 6
    assert coordinates.scan_voltage_y == 9
    assert coordinates.motor_z == 30
    assert coordinates.motor_x == 0
    assert coordinates.motor_y == 0


def test_set_combined_coordinates_motor_mode(coordinates):
    x, y, z = (100, 150, 30)
    coordinates.settings_reader_dict['park_xy_motor'] = False
    assert coordinates.scan_voltage_x == 0
    coordinates.set_combined_coordinates(x, y, z)
    assert coordinates.scan_voltage_x == 0
    assert coordinates.scan_voltage_y == 0
    assert coordinates.motor_z == 30
    assert coordinates.motor_x == 100
    assert coordinates.motor_y == 150
