import tkinter as tk
from tkinter import ttk

import matplotlib
import numpy as np
from matplotlib import patches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from utilities.helper_functions import fit_fig_to_canvas

matplotlib.use("TkAgg")


class StartPage(ttk.Frame):
    name = 'Main'

    def __init__(self, container, session):
        ttk.Frame.__init__(self, container)
        self.session = session
        self.settings = session.settings
        self.bind("<Visibility>", self.on_visibility)
        self.gui = self.build_gui_items()

    def build_gui_items(self):
        session = self.session
        gui = dict()
        gui['frame_left_buttons'] = ttk.Frame(self)
        gui['frame_left_buttons'].grid(row=0, column=0, rowspan=2, sticky='nw')
        gui['button_start'] = ttk.Button(gui['frame_left_buttons'], text="Start Imaging",
                                         command=lambda: session.start_imaging())
        gui['button_start'].grid(row=3, column=0, padx=10, pady=10, sticky='nw')
        gui['button_end'] = ttk.Button(gui['frame_left_buttons'], text="Stop Imaging",
                                       command=lambda: session.stop_imaging())
        gui['button_end'].grid(row=4, column=0, padx=10, pady=10, sticky='nw')
        gui['drift_label'] = tk.Label(self, text="drift placeholder",
                                      font=session.settings.get('large_font'))
        gui['drift_label'].grid(row=0, column=1, padx=10, pady=10, sticky='nw')
        gui['frame_for_canvases'] = ttk.Frame(self)
        gui['frame_for_canvases'].grid(row=1, column=1, columnspan=2, rowspan=2)
        gui['figure_af_images'] = Figure(figsize=(5, 2), dpi=session.settings.get('fig_dpi'))
        gui['figure_af_images'].subplots_adjust(left=0, right=1, bottom=0, wspace=0.02, hspace=0)
        gui['axes_af_images'] = [gui['figure_af_images'].add_subplot(1, 1, 1)]
        gui['canvas_af'] = FigureCanvasTkAgg(gui['figure_af_images'], gui['frame_for_canvases'])
        gui['canvas_af'].show()
        gui['canvas_af'].get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                                highlightbackground='gray')
        gui['canvas_af'].get_tk_widget().grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        gui['canvas_timeline'] = FigureCanvasTkAgg(session.gui.shared_figs['timeline_figure'],
                                                   gui['frame_for_canvases'])
        gui['canvas_timeline'].show()
        gui['canvas_timeline'].get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                                      highlightbackground='gray')
        gui['canvas_timeline'].get_tk_widget().grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        gui['canvas_positions'] = FigureCanvasTkAgg(session.gui.shared_figs['f_positions'],
                                                    gui['frame_for_canvases'])
        gui['canvas_positions'].show()
        gui['canvas_positions'].get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                                       highlightbackground='gray')
        gui['canvas_positions'].get_tk_widget().grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky='nsew')
        return gui

    def on_visibility(self, event):
        fit_fig_to_canvas(self.session.gui.shared_figs['timeline_figure'], self.gui['canvas_timeline'],
                          self.session.settings.get('fig_dpi'))
        fit_fig_to_canvas(self.session.gui.shared_figs['f_positions'], self.gui['canvas_positions'],
                          self.session.settings.get('fig_dpi'))
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
