from app.TkinterTestCase import TkinterTestCase
from app.guis.SettingsPage import SettingsPage
import tkinter as tk


class TestSettingsPage(TkinterTestCase):

    def test_total_channels_entry(self):
        widget = self.app.gui.frames[SettingsPage].gui['entry_total_channels']
        widget.delete(0, tk.END)
        widget.insert(0, '3')
        val = self.app.settings.get('total_channels')
        self.assertEquals(val, 3)
        widget.delete(0, tk.END)
        widget.insert(0, '2')
        val = self.app.settings.get('total_channels')
        self.assertEquals(val, 2)

    def test_drift_correction_channel_entry(self):
        widget = self.app.gui.frames[SettingsPage].gui['entry_drift_channel']
        widget.delete(0, tk.END)
        widget.insert(0, '3')
        val = self.app.settings.get('drift_correction_channel')
        self.assertEquals(val, 3)
        widget.delete(0, tk.END)
        widget.insert(0, '2')
        val = self.app.settings.get('drift_correction_channel')
        self.assertEquals(val, 2)
