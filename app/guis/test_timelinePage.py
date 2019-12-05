from app.TkinterTestCase import TkinterTestCase
import tkinter as tk

from app.guis import TimelinePage


class TestTimelinePage(TkinterTestCase):

    def test_add_timeline_step(self):
        widget = self.app.gui.frames[TimelinePage].gui['entry_total_channels']
        widget.delete(0, tk.END)
        widget.insert(0, '3')
        val = self.app.settings.get('total_channels')
        self.assertEquals(val, 3)
        widget.delete(0, tk.END)
        widget.insert(0, '2')
        val = self.app.settings.get('total_channels')
        self.assertEquals(val, 2)
