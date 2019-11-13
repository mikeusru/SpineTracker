import tkinter as tk
from tkinter import ttk
import numpy as np
from matplotlib import patches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from io_communication.Event import initialize_events
from utilities.helper_functions import fit_fig_to_canvas


class StartPage(ttk.Frame):
    name = 'Main'

    def __init__(self, container, session):
        ttk.Frame.__init__(self, container)
        self.container = container
        self.bind("<Visibility>", self.on_visibility)
        self.settings = {
            'large_font': None,
            'huge_font': None,
            'fig_dpi': 0
        }
        self.gui_vars = {
            'drift_label': None,
            'communication_log': None,
            'display_timer': None
        }
        self.events = initialize_events([
            'start_imaging',
            'stop_imaging'
        ])
        self.shared_figs = None
        self.gui = None

    def build_gui_items(self):
        gui = dict()
        gui['frame_left_buttons'] = ttk.Frame(self)
        gui['frame_left_buttons'].grid(row=0, column=0, rowspan=2, sticky='nw')
        gui['button_start'] = ttk.Button(gui['frame_left_buttons'], text="Start Imaging",
                                         command=lambda: self.events['start_imaging']())
        gui['button_start'].grid(row=3, column=0, padx=10, pady=10, sticky='nw')
        gui['button_end'] = ttk.Button(gui['frame_left_buttons'], text="Stop Imaging",
                                       command=lambda: self.events['stop_imaging']())
        gui['button_end'].grid(row=4, column=0, padx=10, pady=10, sticky='nw')
        gui['drift_label'] = tk.Label(self, textvariable=self.gui_vars['drift_label'],
                                      font=self.settings['large_font'])
        gui['drift_label'].grid(row=0, column=1, padx=10, pady=10, sticky='nw')
        gui['frame_for_canvases'] = ttk.Frame(self)
        gui['frame_for_canvases'].grid(row=1, column=1, columnspan=2, rowspan=2)
        gui['figure_af_images'] = Figure(figsize=(5, 2), dpi=self.settings['fig_dpi'])
        gui['figure_af_images'].subplots_adjust(left=0, right=1, bottom=0, wspace=0.02, hspace=0)
        gui['axes_af_images'] = [gui['figure_af_images'].add_subplot(1, 1, 1)]
        gui['canvas_af'] = FigureCanvasTkAgg(gui['figure_af_images'], gui['frame_for_canvases'])
        gui['canvas_af'].draw()
        gui['canvas_af'].get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                                highlightbackground='gray')
        gui['canvas_af'].get_tk_widget().grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        gui['canvas_timeline'] = FigureCanvasTkAgg(self.shared_figs['timeline_figure'],
                                                   gui['frame_for_canvases'])
        gui['canvas_timeline'].draw()
        gui['canvas_timeline'].get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                                      highlightbackground='gray')
        gui['canvas_timeline'].get_tk_widget().grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        gui['canvas_positions'] = FigureCanvasTkAgg(self.shared_figs['f_positions'],
                                                    gui['frame_for_canvases'])
        gui['canvas_positions'].draw()
        gui['canvas_positions'].get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                                       highlightbackground='gray')
        gui['canvas_positions'].get_tk_widget().grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky='nsew')
        gui['communication_log_label'] = tk.Label(self, textvariable=self.gui_vars['communication_log'],
                                                  font=self.settings['large_font'])
        gui['communication_log_label'].grid(row=3, column=1, columnspan=2, padx=10, pady=10, sticky='nw')
        gui['display_timer_label'] = tk.Label(self, textvariable=self.gui_vars['display_timer'],
                                              font=self.settings['huge_font'])
        gui['display_timer_label'].grid(row=3, column=0, columnspan=1, padx=10, pady=10, sticky='nw')
        self.gui = gui

    def on_visibility(self, event):
        fit_fig_to_canvas(self.shared_figs['timeline_figure'], self.gui['canvas_timeline'],
                          self.settings['fig_dpi'])
        fit_fig_to_canvas(self.shared_figs['f_positions'], self.gui['canvas_positions'],
                          self.settings['fig_dpi'])
        self.update_canvases()

    def display_image_stack(self, current_image):
        image_stack = current_image.image_stack
        a = self.gui['axes_af_images']
        for count, image in enumerate(image_stack):
            a[count].clear()
            a[count].imshow(image)
            a[count].axis('equal')
            a[count].axis('off')
            count += 1

    def indicate_drift_on_images(self, current_image):
        # show best focused image
        max_ind = current_image.drift_x_y_z.focus_list.argmax().item()
        siz = current_image.image_stack[0].shape
        rect = patches.Rectangle((0, 0), siz[0], siz[1], fill=False, linewidth=5, edgecolor='r')
        a = self.gui['axes_af_images']
        a[max_ind].add_patch(rect)
        # add arrow to show shift in x,y
        center = np.array([siz[0] / 2, siz[1] / 2])
        drift_x, drift_y = (current_image.drift_x_y_z.x_pixels, current_image.drift_x_y_z.y_pixels)
        arrow = patches.Arrow(center[1] - drift_x, center[0] - drift_y, drift_x, drift_y, width=10, color='r')
        a[max_ind].add_patch(arrow)

    def update_canvases(self):
        for key in ['canvas_af', 'canvas_timeline', 'canvas_positions']:
            self.gui[key].draw_idle()

    def clear_drift_image_axes(self):
        figure = self.gui['figure_af_images']
        axes = self.gui['axes_af_images']
        for axis in axes.copy():
            axes.remove(axis)
            figure.delaxes(axis)

    def create_drift_image_axes(self, current_image):
        subplot_length = len(current_image.image_stack)
        figure = self.gui['figure_af_images']
        axes = self.gui['axes_af_images']
        for i in range(subplot_length):
            axes.append(figure.add_subplot(1, subplot_length, i + 1))
