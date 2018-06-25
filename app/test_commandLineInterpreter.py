from unittest import TestCase


class TestCommandLineInterpreter(TestCase):

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

    def test_interpret(self):
        self.assertTrue(1==1)

    def test__set_setting(self):
        self.assertTrue(1==1)

