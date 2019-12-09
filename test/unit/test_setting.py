from unittest import TestCase
from unittest.mock import patch, MagicMock

from app.Setting import Setting
import tkinter as tk


def callback_test():
    return True


class GuiVarTest:
    def set(self, value):
        self.value = value

    def get(self):
        return self.value


class TestSetting(TestCase):
    def test__update_dtype(self):
        setting = Setting('test', None, True, '', callback=callback_test, dtype=int)
        setting._update_dtype()
        self.assertEqual(setting.value, 0)
        setting.value = 5
        setting._update_dtype()
        self.assertEqual(setting.value, 5)
        setting.value = '15'
        setting._update_dtype()
        self.assertEqual(setting.value, 15)
        setting.value = 'hi there'
        setting.dtype = str
        setting._update_dtype()
        self.assertEqual(setting.value, 'hi there')

    def test_set(self):
        setting = Setting('test', None, True, '', callback=callback_test, dtype=int)
        setting.set(14)
        self.assertEqual(setting.value, 14)

    def test_get_value(self):
        setting = Setting('test', None, True, 14, callback=callback_test, dtype=int)
        self.assertEqual(setting.get_value(), 14)

