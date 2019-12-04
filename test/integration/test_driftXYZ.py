from unittest import TestCase
import numpy as np

from app.DriftXYZ import DriftXYZ


class TestDriftXYZ(TestCase):

    def test_init(self):
        drift_xyz = DriftXYZ()
        self.assertEqual(drift_xyz.x_pixels, 0)
        self.assertEqual(drift_xyz.x_um, 0.0)
        self.assertEqual(drift_xyz.y_pixels, 0)
        self.assertEqual(drift_xyz.y_um, 0.0)
        self.assertEqual(drift_xyz.z_slices, 0)
        self.assertEqual(drift_xyz.z_um, 0.0)
        self.assertEqual(drift_xyz.focus_list, np.array([]))

    def test_copy(self):
        drift_xyz = DriftXYZ()
        drift_xyz.z_um = 12
        result = drift_xyz.copy()
        self.assertEqual(result.z_um, 12)

    def test_compute_drift_z(self):
        self.fail()

    def test_measure_focus(self):
        self.fail()

    def test_compute_drift_x_y(self):
        self.fail()

    def test_scale_x_y_drift_to_image(self):
        self.fail()
