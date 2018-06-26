from unittest import TestCase


class TkinterTestCase(TestCase):

    app = None

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
        cls.app.gui.destroy()

    def setUp(self):
        """runs code before every test"""
        self.pump_events()

    def tearDown(self):
        """runs code after every test"""
        self.pump_events()

    def pump_events(self):
        import _tkinter
        while self.app.gui.dooneevent(_tkinter.ALL_EVENTS | _tkinter.DONT_WAIT):
            pass
