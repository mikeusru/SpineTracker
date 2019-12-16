import pytest

from app.Timeline import TimelineStepBlock


@pytest.fixture()
def timeline_step_block():
    timeline_step_block = TimelineStepBlock()
    timeline_step_block['start_time'] = 0
    timeline_step_block['end_time'] = timeline_step_block['start_time'] + \
                                      timeline_step_block['period'] * timeline_step_block['iterations']
    return timeline_step_block


def test_is_valid(timeline_step_block):
    assert timeline_step_block.is_valid()
    timeline_step_block['period'] = 0
    assert not timeline_step_block.is_valid()
    timeline_step_block['image_or_uncage'] = 'uncage'
    assert timeline_step_block.is_valid()


def test_shift_start_end_times(timeline_step_block):
    old_end_time = timeline_step_block['end_time']
    timeline_step_block.shift_start_end_times(2)
    assert timeline_step_block['start_time'] == 2
    assert timeline_step_block['end_time'] == old_end_time + 2
