import pytest

from app.AcquiredImage import ReferenceImage, ReferenceImageZoomedOut
from app.Coordinates import Coordinates
from app.Position import Position
from app.Positions import Positions


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
    ref_img = ReferenceImage()
    ref_img_zoomed_out = ReferenceImageZoomedOut()
    positions.create_new_pos(ref_img, ref_img_zoomed_out)
    positions.create_new_pos(ref_img, ref_img_zoomed_out)
    coordinates2 = coordinates.copy()
    coordinates2.motor_x = 50
    positions.set_coordinates(2, coordinates2)
    return positions


def test_set_coordinates(positions):
    coordinates = positions.get_coordinates(2)
    assert coordinates.motor_x == 50
    assert coordinates.scan_voltage_x == 0


def test_create_new_pos(positions):
    assert positions.current_position == 2
    assert positions[1]['coordinates'].motor_x == 0


def test_get_coordinates(positions):
    pos_id = 1
    coordinates = positions.get_coordinates(pos_id)
    assert coordinates.motor_x == 0
    assert coordinates.scan_voltage_x == 0
