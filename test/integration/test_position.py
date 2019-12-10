from unittest import TestCase
from unittest.mock import MagicMock

import numpy as np

from app.Position import Position


class TestPosition(TestCase):
    def test_set_default_roi_pos(self):
        position = Position()
        ref_mock = MagicMock()
        ref_mock.get_shape.return_value = (128, 128, 3)
        position['ref_image'] = ref_mock
        position.set_default_roi_pos()
        np.testing.assert_array_equal(position['roi_x_y'], np.array([64, 64]))
