from unittest import TestCase
from unittest.mock import MagicMock
import pytest
import numpy as np

from app.Coordinates import Coordinates
from app.Position import Position
from app.Positions import Positions


class TestPosition(TestCase):
    def test_set_default_roi_pos(self):
        position = Position()
        ref_mock = MagicMock()
        ref_mock.get_shape.return_value = (128, 128, 3)
        position['ref_image'] = ref_mock
        position.set_default_roi_pos()
        np.testing.assert_array_equal(position['roi_x_y'], np.array([64, 64]))


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


class FakeState:
    def __init__(self):
        self.current_coordinates = None


class FakeSession:

    def __init__(self):
        self.settings = None
        self.state = FakeState()


@pytest.fixture()
def positions(coordinates):
    session = FakeSession()
    session.state.current_coordinates = coordinates
    positions = Positions(session)
    ref_img = np.zeros([128, 128])
    positions.create_new_pos(ref_img, ref_img)
    return positions


def test_get_coordinates(positions):
    pos_id = 0
    positions.get_coordinates(pos_id)
