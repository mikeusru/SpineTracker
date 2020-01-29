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
    return positions

def test_create_new_pos(positions):
    assert positions.current_position == 1

def test_move_to_pos_id():
    # coordinates = self.positions.get_coordinates(pos_id)
    # coordinates.update_to_center()
    # self.communication.move_to_coordinates(coordinates)
    assert False

def test_get_coordinates(positions):
    pos_id = 1
    coordinates = positions.get_coordinates(pos_id)
    assert coordinates.motor_x == 0
