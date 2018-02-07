import tkinter as tk
from tkinter import ttk
import matplotlib

matplotlib.use("TkAgg")


class SettingsPage(ttk.Frame):
    name = 'Settings'

    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller

        self.gui_value_vars = self.define_gui_value_vars()

        def print_args(*args):
                print(args)
        self.macro_resolution_x_string_var.trace_add('write', print_args)

        self.set_default_settings()
        self.gui = self.define_gui_elements()

    def define_gui_value_vars(self):
        # gui_value_vars = dict()
        # gui_value_vars['total_channels_string_var'] = tk.StringVar(self)
        # gui_value_vars['drift_correction_channel_string_var'] = tk.StringVar(self)
        # gui_value_vars['xy_mode_string_var'] = tk.StringVar(self)
        # gui_value_vars['uncaging_roi_toggle_string_var'] = tk.BooleanVar(self)
        # gui_value_vars['macro_resolution_x_string_var'] = tk.StringVar(self)
        # gui_value_vars['macro_resolution_y_string_var'] = tk.StringVar(self)
        # gui_value_vars['normal_resolution_x_string_var'] = tk.StringVar(self)
        # gui_value_vars['normal_resolution_y'] = tk.StringVar(self)
        #
        # gui_value_vars['xy_mode_string_var'].trace('w', self.toggle_xy_mode)
        # gui_value_vars['total_channels_string_var'].trace_add('write', self.update_settings_from_gui_vars)

        return gui_value_vars

    def update_settings_from_gui_vars(self):
        # TODO: This doesn't only have to figure out the value, but also the corresponding settings variable. Maybe the names can be shared with the settings..?
        pass

    def define_gui_elements(self):
        gui = dict()
        gui['total_image_channels_label'] = tk.Label(self, text="Total Image Channels",
                                                     font=self.controller.get_app_param('large_font'))
        gui['total_image_channels_label'].grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        gui['entry_total_channels'] = ttk.Entry(self, textvariable=self.total_channels_string_var)
        gui['entry_total_channels'].grid(row=0, column=1, padx=10, pady=10, sticky='nw')
        gui['drift_correction_channel_label'] = tk.Label(self, text="Drift Correction Channel",
                                                         font=self.controller.get_app_param('large_font'))
        gui['drift_correction_channel_label'].grid(row=1, column=0, sticky='nw', padx=10, pady=10)
        gui['entry_drift_channel'] = ttk.Entry(self, textvariable=self.drift_correction_channel_string_var)
        gui['entry_drift_channel'].grid(row=1, column=1, padx=10, pady=10, sticky='nw')
        gui['scan_shift_rb'] = ttk.Radiobutton(self, text='Scan Shift for X,Y', variable=self.xy_mode_string_var,
                                               value='Galvo')
        gui['scan_shift_rb'].grid(row=2, column=0, sticky='nw', pady=10, padx=10)
        gui['motor_rb'] = ttk.Radiobutton(self, text='Motor for X,Y', variable=self.xy_mode_string_var,
                                          value='Motor')
        gui['motor_rb'].grid(row=3, column=0, sticky='nw', pady=10, padx=10)
        gui['show_uncaging_roi_cb'] = ttk.Checkbutton(self, text="Show Unaging ROI",
                                                      variable=self.uncaging_roi_toggle_string_var)
        gui['show_uncaging_roi_cb'].grid(row=4, column=0, sticky='nw', pady=10, padx=10)
        gui['macro_resolution_label'] = tk.Label(self, text="Macro Imaging Resolution (X,Y pixels)",
                                                         font=self.controller.get_app_param('large_font'))
        gui['macro_resolution_label'].grid(row=5, column=0, sticky='nw', padx=10, pady=10)
        gui['entry_macro_resolution_x'] = ttk.Entry(self, textvariable=self.macro_resolution_x_string_var)
        gui['entry_macro_resolution_x'].grid(row=5, column=1, padx=10, pady=10, sticky='nw')
        gui['entry_macro_resolution_y'] = ttk.Entry(self, textvariable=self.macro_resolution_y_string_var)
        gui['entry_macro_resolution_y'].grid(row=5, column=2, padx=10, pady=10, sticky='nw')
        gui['normal_resolution_label'] = tk.Label(self, text="Normal Imaging Resolution (X,Y pixels)",
                                                         font=self.controller.get_app_param('large_font'))
        gui['normal_resolution_label'].grid(row=6, column=0, sticky='nw', padx=10, pady=10)
        gui['entry_normal_resolution_x'] = ttk.Entry(self, textvariable=self.normal_resolution_x_string_var)
        gui['entry_normal_resolution_x'].grid(row=6, column=1, padx=10, pady=10, sticky='nw')
        gui['entry_normal_resolution_y'] = ttk.Entry(self, textvariable=self.normal_resolution_y_string_var)
        gui['entry_normal_resolution_y'].grid(row=6, column=2, padx=10, pady=10, sticky='nw')
        return gui

    def set_default_settings(self):
        self.total_channels_string_var.set(self.controller.get_settings('total_channels', 2))
        self.drift_correction_channel_string_var.set(self.controller.get_settings('drift_correction_channel', 1))
        self.xy_mode_string_var.set("Galvo")
        self.macro_resolution_x_string_var.set(self.controller.get_settings('macro_resolution_x'))
        self.macro_resolution_y_string_var.set(self.controller.get_settings('macro_resolution_y'))
        self.normal_resolution_x_string_var.set(self.controller.get_settings('normal_resolution_x'))
        self.normal_resolution_y_string_var.set(self.controller.get_settings('normal_resolution_y'))
        self.uncaging_roi_toggle_string_var.set(True)

    def settings_trace(self,*args):
        # TODO: Create dict for all stringvars to search through them, identify the correct one, and then get its value to update the settings

        pass

    def toggle_xy_mode(self, *args):
        mode = self.xy_mode_string_var.get()
        self.controller.print_status(mode)
        if mode == 'Galvo':
            self.controller.set_settings('park_xy_motor', True)
        else:
            self.controller.set_settings('park_xy_motor', False)
