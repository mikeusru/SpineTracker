# import sys
# sys.path.append('../')

import unittest

import numpy as np

from utilities.math_helpers import round_math, blank_to_none, none_to_blank, compute_drift


class TestMath(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """runs once before all tests"""
        print('setupClass')

    @classmethod
    def tearDownClass(cls):
        """runs once after all tests"""
        print('tearDownClass')

    def setUp(self):
        """runs code before every test"""
        pass

    def tearDown(self):
        """runs code after every test"""
        pass

    def test_round_math(self):
        result = round_math(5.57, 1)
        self.assertEqual(result, 5.6)
        result = round_math(6.57, 1)
        self.assertEqual(result, 6.6)
        result = round_math(4.3123241, 2)
        self.assertEqual(result, 4.31)
        result = round_math(5.54543, 0)
        self.assertEqual(result, 6)

    def test_blank_to_none(self):
        result = blank_to_none('')
        self.assertEqual(result, None)
        result = blank_to_none('32131')
        self.assertEqual(result, '32131')
        result = blank_to_none('gfdgfd')
        self.assertEqual(result, 'gfdgfd')

    def test_none_to_blank(self):
        result = none_to_blank('')
        self.assertEqual(result, '')
        result = none_to_blank('fsdfsd')
        self.assertEqual(result, 'fsdfsd')
        result = none_to_blank(None)
        self.assertEqual(result, '')
        result = none_to_blank(432432.6564)
        self.assertEqual(result, 432432.6564)

    def test_compute_drift(self):
        image_ref = np.zeros([25, 25], dtype=np.uint8)
        image_ref[13, 13] = 100
        image_drifted = np.zeros([25, 25], dtype=np.uint8)
        image_drifted[19, 10] = 100
        result = compute_drift(image_ref, image_drifted)
        self.assertEqual(result['shiftx'], 2.5)
        self.assertEqual(result['shifty'], -6.5)


if __name__ == '__main__':
    unittest.main()
