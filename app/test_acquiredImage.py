import numpy as np
from unittest import TestCase
from app.AcquiredImage import AcquiredImage


class TestAcquiredImage(TestCase):

    def setUp(self):
        self.acquired_image = AcquiredImage()
        self.acquired_image.image_file_path = '../test/images/Test_Ch1_111.tif'
        self.acquired_image.total_chan = 1
        self.acquired_image.drift_chan = 1
        self.acquired_image.fov_x_y = np.array([250, 250])

    def test_load(self):
        self.acquired_image.load()
        print(self.acquired_image.image_stack.shape)
        image_shape = self.acquired_image.image_stack.shape
        self.assertEqual((128,128,3), image_shape)

    # def test_set_zoom(self):
    #     self.fail()
    #
    # def test_calc_x_y_z_drift(self):
    #     self.fail()
    #
    # def test_get_max_projection(self):
    #     self.fail()
    #
    # def test_calc_x_y_drift(self):
    #     self.fail()
    #
    # def test_get_shape(self):
    #     self.fail()
    #
    # def test_set_stack(self):
    #     self.fail()
