import tkinter as tk
from tkinter import ttk
import matplotlib

matplotlib.use("TkAgg")


class SettingsPage(ttk.Frame):
    name = 'Settings'

    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Total Image Channels", font=self.controller.get_app_param('large_font'))
        label.grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        self.totalChannelsVar = tk.StringVar(self)
        entry_total_channels = ttk.Entry(self, textvariable=self.totalChannelsVar)
        entry_total_channels.grid(row=0, column=1, padx=10, pady=10, sticky='nw')
        label2 = tk.Label(self, text="Drift Correction Channel", font=self.controller.get_app_param('large_font'))
        label2.grid(row=1, column=0, sticky='nw', padx=10, pady=10)
        self.driftCorrectionChannelVar = tk.StringVar(self)
        entry_drift_channel = ttk.Entry(self, textvariable=self.driftCorrectionChannelVar)
        entry_drift_channel.grid(row=1, column=1, padx=10, pady=10, sticky='nw')
        self.xy_mode = tk.StringVar(self)
        self.xy_mode.trace('w', self.toggle_xy_mode)
        rb1 = ttk.Radiobutton(self, text='Scan Shift for X,Y', variable=self.xy_mode,
                              value='Galvo')
        rb1.grid(row=2, column=0, sticky='nw', pady=10, padx=10)
        rb2 = ttk.Radiobutton(self, text='Motor for X,Y', variable=self.xy_mode,
                              value='Motor')
        rb2.grid(row=3, column=0, sticky='nw', pady=10, padx=10)
        self.uncaging_roi_toggle = tk.BooleanVar(self)
        cb = ttk.Checkbutton(self, text="Show Unaging ROI",
                             variable=self.uncaging_roi_toggle)
        cb.grid(row=4, column=0, sticky='nw', pady=10, padx=10)
        self.set_default_settings()

    def set_default_settings(self):
        self.totalChannelsVar.set(self.controller.get_settings('totalChannels',2))
        self.driftCorrectionChannelVar.set(self.controller.get_settings('driftCorrectionChannel',1))
        self.xy_mode.set("Galvo")
        self.uncaging_roi_toggle.set(True)

    def toggle_xy_mode(self, *args):
        mode = self.xy_mode.get()
        self.controller.print_status(mode)
        if mode == 'Galvo':
            self.controller.parkXYmotor = True
        else:
            self.controller.parkXYmotor = False
