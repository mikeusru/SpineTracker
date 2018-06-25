from unittest import TestCase


class TestSpineTracker(TestCase):

    @classmethod
    def setUpClass(cls):
        """runs once before all tests"""
        print('setupClass')
        from app.main import SpineTracker
        cls.app = SpineTracker()

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

    def test_mainloop(self):
        self.app.mainloop()