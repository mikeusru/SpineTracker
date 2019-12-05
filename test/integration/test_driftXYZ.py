from unittest import TestCase
import numpy as np

from app.DriftXYZ import DriftXYZ
from unittest.mock import patch


class TestDriftXYZ(TestCase):

    def test_init(self):
        drift_xyz = DriftXYZ()
        self.assertEqual(drift_xyz.x_pixels, 0)
        self.assertEqual(drift_xyz.x_um, 0.0)
        self.assertEqual(drift_xyz.y_pixels, 0)
        self.assertEqual(drift_xyz.y_um, 0.0)
        self.assertEqual(drift_xyz.z_slices, 0)
        self.assertEqual(drift_xyz.z_um, 0.0)
        np.testing.assert_array_equal(drift_xyz.focus_list, np.array([]))

    def test_copy(self):
        drift_xyz = DriftXYZ()
        drift_xyz.z_um = 12
        result = drift_xyz.copy()
        self.assertEqual(result.z_um, 12)

    def test_compute_drift_z_even(self):
        drift_xyz = DriftXYZ()
        image_stack = [1, 2, 3, 4]
        zstep = 3
        with patch.object(DriftXYZ, 'measure_focus') as mocked_measure_focus:
            mocked_measure_focus.side_effect = (0, 2, 4, 1)
            drift_xyz.compute_drift_z(image_stack, zstep)
        self.assertEqual(drift_xyz.z_slices, 0)
        np.testing.assert_array_equal(drift_xyz.focus_list, np.array([0, 2, 4, 1]))
        self.assertEqual(drift_xyz.z_um, 0)

    def test_compute_drift_z_odd(self):
        drift_xyz = DriftXYZ()
        image_stack = [1, 2, 3, 4, 5]
        zstep = 3
        with patch.object(DriftXYZ, 'measure_focus') as mocked_measure_focus:
            mocked_measure_focus.side_effect = (1, 10, 2, 4, 1)
            drift_xyz.compute_drift_z(image_stack, zstep)
        self.assertEqual(drift_xyz.z_slices, -1)
        np.testing.assert_array_equal(drift_xyz.focus_list, np.array([1, 10, 2, 4, 1]))
        self.assertEqual(drift_xyz.z_um, -3)

    def test_measure_focus(self):
        drift_xyz = DriftXYZ()
        img = np.ones([128, 128])
        focus = drift_xyz.measure_focus(img)
        self.assertEqual(focus, 64.05830055475235)

    def test_compute_drift_x_y(self):
        drift_xyz = DriftXYZ()
        img_ref = np.zeros([10, 10])
        img_ref[5, 5] = 1
        img = np.zeros([10, 10])
        img[8, 3] = 1
        drift_xyz.compute_pixel_drift_x_y(img_ref, img)
        self.assertEqual(drift_xyz.x_pixels, 2)
        self.assertEqual(drift_xyz.y_pixels, -3)

    def test_scale_x_y_drift_to_image(self):
        drift_xyz = DriftXYZ()
        position = {'scan_voltage_multiplier': 1, 'fov_xy': [250, 250], 'rotation': 0}
        zoom = 10
        image_shape = (128, 128)
        drift_xyz.x_pixels = 5
        drift_xyz.y_pixels = -11
        drift_xyz.scale_x_y_drift_to_image(position, zoom, image_shape)
        self.assertEqual(round(drift_xyz.x_um, 3), -.977)
        self.assertEqual(round(drift_xyz.y_um, 3), 2.148)
