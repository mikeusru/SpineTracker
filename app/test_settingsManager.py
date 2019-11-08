from unittest import TestCase



class TestSettingsManager(TestCase):
    @classmethod
    def setUpClass(cls):
        """runs once before all tests"""
        print('setupClass')
        from app.main import SpineTracker
        cls.container = SpineTracker()
        from app.SettingsManager import SettingsManager
        cls.settings = SettingsManager(cls.container)

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

    def test_initialize_settings(self):
        self.settings.initialize_settings()


    # def test_set_default_callbacks(self):
    #     self.fail()
    #
    # def test_default_trace(self):
    #     self.fail()
    #
    # def test_update_value(self):
    #     self.fail()
    #
    # def test__exists(self):
    #     self.fail()
    #
    # def test_set(self):
    #     self.fail()
    #
    # def test_get(self):
    #     self.fail()
    #
    # def test_get_gui_var(self):
    #     self.fail()
    #
    # def test_load_settings(self):
    #     self.fail()
    #
    # def test_update_with_loaded_dict(self):
    #     self.fail()
    #
    # def test_save_settings(self):
    #     self.fail()
    #
    # def test__get_file_name(self):
    #     self.fail()
    #
    # def test_update_gui_from_settings(self):
    #     self.fail()
