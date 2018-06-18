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

    def test_set(self):
        pass



if __name__ == '__main__':
    unittest.main()