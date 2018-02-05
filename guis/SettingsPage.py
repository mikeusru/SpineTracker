import tkinter as tk
from tkinter import ttk
import matplotlib

matplotlib.use("TkAgg")


class SettingsPage(ttk.Frame):
    name = 'Settings'

    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.total_channels_var = tk.StringVar(self)
        self.drift_correction_channel_var = tk.StringVar(self)
        self.xy_mode_var = tk.StringVar(self)
        self.xy_mode_var.trace('w', self.toggle_xy_mode)
        self.uncaging_roi_toggle_var = tk.BooleanVar(self)
        self.gui = dict()
        self.gui['total_image_channels_label'] = tk.Label(self, text="Total Image Channels",
                                                          font=self.controller.get_app_param('large_font'))
        self.gui['total_image_channels_label'].grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        self.gui['entry_total_channels'] = ttk.Entry(self, textvariable=self.total_channels_var)
        self.gui['entry_total_channels'].grid(row=0, column=1, padx=10, pady=10, sticky='nw')
        self.gui['drift_correction_channel_label'] = tk.Label(self, text="Drift Correction Channel",
                                                              font=self.controller.get_app_param('large_font'))
        self.gui['drift_correction_channel_label'].grid(row=1, column=0, sticky='nw', padx=10, pady=10)
        self.gui['entry_drift_channel'] = ttk.Entry(self, textvariable=self.drift_correction_channel_var)
        self.gui['entry_drift_channel'].grid(row=1, column=1, padx=10, pady=10, sticky='nw')

        self.gui['scan_shift_rb'] = ttk.Radiobutton(self, text='Scan Shift for X,Y', variable=self.xy_mode_var,
                                                    value='Galvo')
        self.gui['scan_shift_rb'].grid(row=2, column=0, sticky='nw', pady=10, padx=10)
        self.gui['motor_rb'] = ttk.Radiobutton(self, text='Motor for X,Y', variable=self.xy_mode_var,
                                               value='Motor')
        self.gui['motor_rb'].grid(row=3, column=0, sticky='nw', pady=10, padx=10)
        self.gui['show_uncaging_roi_cb'] = ttk.Checkbutton(self, text="Show Unaging ROI",
                                                           variable=self.uncaging_roi_toggle_var)
        self.gui['show_uncaging_roi_cb'].grid(row=4, column=0, sticky='nw', pady=10, padx=10)
        self.set_default_settings()

    def set_default_settings(self):
        self.total_channels_var.set(self.controller.get_settings('totalChannels', 2))
        self.drift_correction_channel_var.set(self.controller.get_settings('driftCorrectionChannel', 1))
        self.xy_mode_var.set("Galvo")
        self.uncaging_roi_toggle_var.set(True)

    def toggle_xy_mode(self, *args):
        mode = self.xy_mode_var.get()
        self.controller.print_status(mode)
        if mode == 'Galvo':
            self.controller.set_settings_var('park_xy_motor', True)
        else:
            self.controller.set_settings_var('park_xy_motor', False)
