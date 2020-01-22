import os
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import asksaveasfilename, askopenfilename

from app.io_communication.Event import initialize_events


class SettingsPage(ttk.Frame):
    name = 'Settings'

    def __init__(self, container, session):
        ttk.Frame.__init__(self, container)
        self.settings = {
            'large_font': None,
            'normal_font': None,
        }
        self.gui_vars = {
            'total_channels': None,
            'drift_correction_channel': None,
            'park_xy_motor': None,
            'uncaging_roi_toggle': None,
            'macro_resolution_x': None,
            'macro_resolution_y': None,
            'normal_resolution_x': None,
            'normal_resolution_y': None,
            'manual_fov_toggle': None,
            'fov_x': None,
            'fov_y': None,
            'invert_scan_shift_x': None,
            'invert_scan_shift_y': None,
            'invert_motor_x': None,
            'invert_motor_y': None,
        }
        self.events = initialize_events([
            'save_settings',
            'load_settings'
        ])
        self.gui = None

    def build_gui_items(self):
        gui = dict()
        gui['total_image_channels_label'] = tk.Label(self, text="Total Image Channels",
                                                     font=self.settings['large_font'])
        gui['total_image_channels_label'].grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        gui['entry_total_channels'] = ttk.Entry(self,
                                                textvariable=self.gui_vars['total_channels'])
        gui['entry_total_channels'].grid(row=0, column=1, padx=10, pady=10, sticky='nw')
        gui['save_settings_button'] = tk.Button(self, text="Save Settings As...",
                                                font=self.settings['normal_font'],
                                                command=self.save_settings_as)
        gui['save_settings_button'].grid(row=0, column=3, sticky='ne', padx=10, pady=10)
        gui['load_settings_button'] = tk.Button(self, text="Load Settings",
                                                font=self.settings['normal_font'],
                                                command=self.load_settings)
        gui['load_settings_button'].grid(row=1, column=3, sticky='ne', padx=10, pady=10)
        gui['drift_correction_channel_label'] = tk.Label(self, text="Drift Correction Channel",
                                                         font=self.settings['large_font'])
        gui['drift_correction_channel_label'].grid(row=1, column=0, sticky='nw', padx=10, pady=10)
        gui['entry_drift_channel'] = ttk.Entry(self, textvariable=self.gui_vars['drift_correction_channel'])
        gui['entry_drift_channel'].grid(row=1, column=1, padx=10, pady=10, sticky='nw')

        gui['scan_motor_frame'] = ttk.Frame(self)
        gui['scan_motor_frame'].grid(column=0, row=2, sticky='nw')

        gui['scan_shift_rb'] = ttk.Radiobutton(gui['scan_motor_frame'], text='Scan Shift for X,Y',
                                               variable=self.gui_vars['park_xy_motor'],
                                               value=True)
        gui['scan_shift_rb'].grid(row=0, column=0, sticky='nw', pady=10, padx=10)
        gui['invert_scan_shift_label'] = tk.Label(gui['scan_motor_frame'], text="Invert Scan Shift: ",
                                                  font=self.settings['normal_font'])
        gui['invert_scan_shift_label'].grid(row=0, column=1, sticky='nw', padx=10, pady=10)
        gui['invert_scan_shift_x_cb'] = ttk.Checkbutton(gui['scan_motor_frame'], text="X",
                                                        variable=self.gui_vars['invert_scan_shift_x'])
        gui['invert_scan_shift_x_cb'].grid(row=0, column=2, sticky='nw', pady=10, padx=10)
        gui['invert_scan_shift_y_cb'] = ttk.Checkbutton(gui['scan_motor_frame'], text="Y",
                                                        variable=self.gui_vars['invert_scan_shift_y'])
        gui['invert_scan_shift_y_cb'].grid(row=0, column=3, sticky='nw', pady=10, padx=10)
        gui['motor_rb'] = ttk.Radiobutton(gui['scan_motor_frame'], text='Motor for X,Y',
                                          variable=self.gui_vars['park_xy_motor'],
                                          value=False)
        gui['motor_rb'].grid(row=1, column=0, sticky='nw', pady=10, padx=10)

        gui['invert_motor_label'] = tk.Label(gui['scan_motor_frame'], text="Invert Motor: ",
                                                  font=self.settings['normal_font'])
        gui['invert_motor_label'].grid(row=1, column=1, sticky='nw', padx=10, pady=10)
        gui['invert_motor_x_cb'] = ttk.Checkbutton(gui['scan_motor_frame'], text="X",
                                                        variable=self.gui_vars['invert_motor_x'],state='disabled')
        gui['invert_motor_x_cb'].grid(row=1, column=2, sticky='nw', pady=10, padx=10)
        gui['invert_motor_y_cb'] = ttk.Checkbutton(gui['scan_motor_frame'], text="Y",
                                                        variable=self.gui_vars['invert_motor_y'],state='disabled')
        gui['invert_motor_y_cb'].grid(row=1, column=3, sticky='nw', pady=10, padx=10)

        gui['show_uncaging_roi_cb'] = ttk.Checkbutton(self, text="Show Uncaging ROI",
                                                      variable=self.gui_vars['uncaging_roi_toggle'])
        gui['show_uncaging_roi_cb'].grid(row=4, column=0, sticky='nw', pady=10, padx=10)

        gui['macro_resolution_label'] = tk.Label(self, text="Macro Imaging Resolution (X,Y pixels)",
                                                 font=self.settings['large_font'])
        gui['macro_resolution_label'].grid(row=5, column=0, sticky='nw', padx=10, pady=10)

        gui['entry_macro_resolution_x'] = ttk.Entry(self, textvariable=self.gui_vars['macro_resolution_x'])
        gui['entry_macro_resolution_x'].grid(row=5, column=1, padx=10, pady=10, sticky='nw')

        gui['entry_macro_resolution_y'] = ttk.Entry(self, textvariable=self.gui_vars['macro_resolution_x'])
        gui['entry_macro_resolution_y'].grid(row=5, column=2, padx=10, pady=10, sticky='nw')

        gui['normal_resolution_label'] = tk.Label(self, text="Normal Imaging Resolution (X,Y pixels)",
                                                  font=self.settings['large_font'])
        gui['normal_resolution_label'].grid(row=6, column=0, sticky='nw', padx=10, pady=10)

        gui['entry_normal_resolution_x'] = ttk.Entry(self, textvariable=self.gui_vars['normal_resolution_x'])

        gui['entry_normal_resolution_x'].grid(row=6, column=1, padx=10, pady=10, sticky='nw')
        gui['entry_normal_resolution_y'] = ttk.Entry(self, textvariable=self.gui_vars['normal_resolution_y'])
        gui['entry_normal_resolution_y'].grid(row=6, column=2, padx=10, pady=10, sticky='nw')
        gui['set_fov_manually_cb'] = ttk.Checkbutton(self, text="Manually Set Field of View",
                                                     variable=self.gui_vars['manual_fov_toggle'])
        gui['set_fov_manually_cb'].grid(row=7, column=0, sticky='nw', pady=10, padx=10)
        gui['fov_size_label'] = tk.Label(self, text="Field of View (X,Y µm)",
                                         font=self.settings['large_font'])
        gui['fov_size_label'].grid(row=8, column=0, sticky='nw', padx=10, pady=10)

        gui['entry_fov_x'] = ttk.Entry(self, textvariable=self.gui_vars['fov_x'])

        gui['entry_fov_x'].grid(row=8, column=1, padx=10, pady=10, sticky='nw')
        gui['entry_fov_y'] = ttk.Entry(self, textvariable=self.gui_vars['fov_x'])
        gui['entry_fov_y'].grid(row=8, column=2, padx=10, pady=10, sticky='nw')

        return gui

    def toggle_fov_mode(self):
        var = self.gui_vars['manual_fov_toggle']
        if var:
            self.enable_fov_entry()
        else:
            self.disable_fov_entry()

    def disable_fov_entry(self):
        self.gui['entry_fov_x'].configure(state='disable')
        self.gui['entry_fov_y'].configure(state='disable')

    def enable_fov_entry(self):
        self.gui['entry_fov_x'].configure(state='enable')
        self.gui['entry_fov_y'].configure(state='enable')

    def save_settings_as(self):
        path = asksaveasfilename(initialfile=os.path.expanduser("") + "user_settings.p",
                                 title="Select file",
                                 filetypes=(("pickle file", ".p"),),
                                 defaultextension='.p')
        self.events['save_settings'](path)

    def load_settings(self):
        path = askopenfilename(initialdir=os.path.expanduser(""),
                               title="Select Settings File",
                               filetypes=(("pickle file", "*.p"),))
        self.events['load_settings'](path)
