import pytest

from app.Timeline import TimelineStepBlock


@pytest.fixture()
def timeline_step_block():
    timeline_step_block = TimelineStepBlock()
    return timeline_step_block


def test_is_valid(timeline_step_block):
    assert timeline_step_block.is_valid()
    timeline_step_block['period'] = 0
    assert not timeline_step_block.is_valid()
    timeline_step_block['image_or_uncage'] = 'uncage'
    assert timeline_step_block.is_valid()


def test_shift_start_end_times():
    pass


def test_print_step_info():
    pass
