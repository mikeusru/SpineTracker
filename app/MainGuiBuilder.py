"""
@author: smirnovm
"""
from matplotlib.figure import Figure

from guis.PositionsPage import PositionsPage
from guis.SettingsPage import SettingsPage
from guis.StartPage import StartPage
from guis.TimelinePage import TimelinePage
import tkinter as tk
from tkinter import ttk


class MainGuiBuilder(tk.Tk):

    def __init__(self, settings):
        self.settings = settings
        tk.Tk.__init__(self)
        tk.Tk.iconbitmap(self, default="../images/crabIco.ico")  # icon doesn't work
        tk.Tk.wm_title(self, "SpineTracker")
        tk.Tk.geometry(self, newGeometry='1000x600+200+200')
        self.container = ttk.Notebook(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.frames = self.build_frames()
        self.shared_figs = self.build_shared_figs()

    def build_frames(self):
        frames = {}
        for F in (StartPage, SettingsPage, PositionsPage, TimelinePage):
            frame = F(self.container, self)
            frames[F] = frame
            self.container.add(frame, text=F.name)
        return frames

    def build_shared_figs(self):
        fig_dpi = self.settings.get('fig_dpi')
        return SharedFigs(fig_dpi)


class SharedFigs(dict):

    def __init__(self, fig_dpi, *args, **kwargs):
        super(SharedFigs, self).__init__()

        # Shared Timeline Figure
        self['timeline_figure'] = Figure(figsize=(5, 2), dpi=fig_dpi)
        self['timeline_figure'].set_tight_layout(True)
        self['timeline_axis'] = self['timeline_figure'].add_subplot(111)

        # Shared Positions Figure
        self['f_positions'] = Figure(figsize=(3, 3), dpi=fig_dpi)
        self['f_positions'].subplots_adjust(left=0, right=1, bottom=0, top=1)
        self['f_positions'].set_tight_layout(True)
        self['f_positions'].set_size_inches(4, 4)

# if __name__ == "__main__":
#     app = MainGuiBuilder()
#     app.mainloop()
