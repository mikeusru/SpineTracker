import tkinter as tk
from tkinter import ttk
import matplotlib

matplotlib.use("TkAgg")


class SettingsPage(ttk.Frame):
    name = 'Settings'

    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.gui = self.define_gui_elements()

    def define_gui_elements(self):
        gui = dict()
        gui['total_image_channels_label'] = tk.Label(self, text="Total Image Channels",
                                                     font=self.controller.settings.get('large_font'))
        gui['total_image_channels_label'].grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        gui['entry_total_channels'] = ttk.Entry(self,
                                                textvariable=self.controller.gui_vars['total_channels_string_var'])
        gui['entry_total_channels'].grid(row=0, column=1, padx=10, pady=10, sticky='nw')
        gui['drift_correction_channel_label'] = tk.Label(self, text="Drift Correction Channel",
                                                         font=self.controller.settings.get('large_font'))
        gui['drift_correction_channel_label'].grid(row=1, column=0, sticky='nw', padx=10, pady=10)
        gui['entry_drift_channel'] = ttk.Entry(self, textvariable=self.controller.gui_vars[
            'drift_correction_channel_string_var'])
        gui['entry_drift_channel'].grid(row=1, column=1, padx=10, pady=10, sticky='nw')
        gui['scan_shift_rb'] = ttk.Radiobutton(self, text='Scan Shift for X,Y',
                                               variable=self.controller.gui_vars['park_xy_motor_bool_var'],
                                               value=True)
        gui['scan_shift_rb'].grid(row=2, column=0, sticky='nw', pady=10, padx=10)
        gui['motor_rb'] = ttk.Radiobutton(self, text='Motor for X,Y',
                                          variable=self.controller.gui_vars['park_xy_motor_bool_var'],
                                          value=False)
        gui['motor_rb'].grid(row=3, column=0, sticky='nw', pady=10, padx=10)
        gui['show_uncaging_roi_cb'] = ttk.Checkbutton(self, text="Show Uncaging ROI",
                                                      variable=self.controller.gui_vars[
                                                          'uncaging_roi_toggle_bool_var'])
        gui['show_uncaging_roi_cb'].grid(row=4, column=0, sticky='nw', pady=10, padx=10)

        gui['macro_resolution_label'] = tk.Label(self, text="Macro Imaging Resolution (X,Y pixels)",
                                                 font=self.controller.settings.get('large_font'))
        gui['macro_resolution_label'].grid(row=5, column=0, sticky='nw', padx=10, pady=10)

        gui['entry_macro_resolution_x'] = ttk.Entry(self, textvariable=self.controller.gui_vars[
            'macro_resolution_x_string_var'])
        gui['entry_macro_resolution_x'].grid(row=5, column=1, padx=10, pady=10, sticky='nw')

        gui['entry_macro_resolution_y'] = ttk.Entry(self, textvariable=self.controller.gui_vars[
            'macro_resolution_y_string_var'])
        gui['entry_macro_resolution_y'].grid(row=5, column=2, padx=10, pady=10, sticky='nw')

        gui['normal_resolution_label'] = tk.Label(self, text="Normal Imaging Resolution (X,Y pixels)",
                                                  font=self.controller.settings.get('large_font'))
        gui['normal_resolution_label'].grid(row=6, column=0, sticky='nw', padx=10, pady=10)

        gui['entry_normal_resolution_x'] = ttk.Entry(self, textvariable=self.controller.gui_vars[
            'normal_resolution_x_string_var'])

        gui['entry_normal_resolution_x'].grid(row=6, column=1, padx=10, pady=10, sticky='nw')
        gui['entry_normal_resolution_y'] = ttk.Entry(self, textvariable=self.controller.gui_vars[
            'normal_resolution_y_string_var'])
        gui['entry_normal_resolution_y'].grid(row=6, column=2, padx=10, pady=10, sticky='nw')
        return gui
