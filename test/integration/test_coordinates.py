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
