import tkinter as tk
from tkinter import ttk
import matplotlib
from flow.PositionTimer import PositionTimer
from guis.PositionsPage import PositionsPage
from utilities.helper_functions import fit_fig_to_canvas
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading

matplotlib.use("TkAgg")


class StartPage(ttk.Frame):
    name = 'Main'

    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.bind("<Visibility>", self.on_visibility)
        self.gui = dict()
        self.gui['frame_left_buttons'] = ttk.Frame(self)
        self.gui['frame_left_buttons'].grid(row=0, column=0, rowspan=2, sticky='nw')
        self.gui['button_load_test'] = ttk.Button(self.gui['frame_left_buttons'], text="Load Test Image",
                                                  command=lambda: controller.load_test_image(self))
        self.gui['button_load_test'].grid(row=0, column=0, padx=10, pady=10, sticky='nw')
        self.gui['button_load_test_ref_image'] = ttk.Button(self.gui['frame_left_buttons'], text="Load Test Ref Image",
                                                            command=lambda: controller.load_test_ref_image(self))
        self.gui['button_load_test_ref_image'].grid(row=1, column=0, padx=10, pady=10, sticky='nw')
        self.gui['button_run_drift_correction'] = ttk.Button(self.gui['frame_left_buttons'],
                                                             text="Run Drift Correction",
                                                             command=lambda: controller.run_xyz_drift_correction(1))
        self.gui['button_run_drift_correction'].grid(row=2, column=0, padx=10, pady=10, sticky='nw')
        self.gui['button_start'] = ttk.Button(self.gui['frame_left_buttons'], text="Start Imaging",
                                              command=lambda: self.start_imaging())
        self.gui['button_start'].grid(row=3, column=0, padx=10, pady=10, sticky='nw')
        self.gui['button_end'] = ttk.Button(self.gui['frame_left_buttons'], text="Stop Imaging",
                                            command=lambda: self.stop_imaging())
        self.gui['button_end'].grid(row=4, column=0, padx=10, pady=10, sticky='nw')
        self.gui['drift_label'] = tk.Label(self, text="drift placeholder",
                                           font=controller.get_app_param('large_font'))
        self.gui['drift_label'].grid(row=0, column=1, padx=10, pady=10, sticky='nw')
        self.gui['frame_for_canvases'] = ttk.Frame(self)
        self.gui['frame_for_canvases'].grid(row=1, column=1, columnspan=2, rowspan=2)
        self.gui['figure_af_images'] = Figure(figsize=(5, 2), dpi=controller.get_app_param('fig_dpi'))
        self.gui['figure_af_images'].subplots_adjust(left=0, right=1, bottom=0, wspace=0.02, hspace=0)
        self.gui['axes_af_images'] = [self.gui['figure_af_images'].add_subplot(1, 1, 1)]
        self.gui['canvas_af'] = FigureCanvasTkAgg(self.gui['figure_af_images'], self.gui['frame_for_canvases'])
        self.gui['canvas_af'].show()
        self.gui['canvas_af'].get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                                     highlightbackground='gray')
        self.gui['canvas_af'].get_tk_widget().grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        self.gui['canvas_timeline'] = FigureCanvasTkAgg(self.controller.shared_figs['f_timeline'],
                                                        self.gui['frame_for_canvases'])
        self.gui['canvas_timeline'].show()
        self.gui['canvas_timeline'].get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                                           highlightbackground='gray')
        self.gui['canvas_timeline'].get_tk_widget().grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        self.gui['canvas_positions'] = FigureCanvasTkAgg(self.controller.shared_figs['f_positions'],
                                                         self.gui['frame_for_canvases'])
        self.gui['canvas_positions'].show()
        self.gui['canvas_positions'].get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                                            highlightbackground='gray')
        self.gui['canvas_positions'].get_tk_widget().grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky='nsew')
        self.posTimers = {}

    def on_visibility(self, event):
        fit_fig_to_canvas(self.controller.shared_figs['f_timeline'], self.gui['canvas_timeline'],
                          self.controller.get_app_param('fig_dpi'))
        fit_fig_to_canvas(self.controller.shared_figs['f_positions'], self.gui['canvas_positions'],
                          self.controller.get_app_param('fig_dpi'))
        for key in ['canvas_af', 'canvas_timeline', 'canvas_positions']:
            self.gui[key].draw_idle()

    def start_imaging(self):
        # get scan angle conversion properties
        self.controller.get_scan_props()
        # this probably needs to move somewhere else later
        self.controller.set_zoom(float(self.controller.frames[PositionsPage].imagingZoom.get()))
        # set up timers
        self.posTimers = {}
        with self.controller.timerStepsQueue.mutex:
            self.controller.timerStepsQueue.queue.clear()
        individual_steps = self.controller.individualTimelineSteps
        for posID in individual_steps:
            self.posTimers[posID] = PositionTimer(self.controller, individual_steps[posID],
                                                  self.controller.add_step_to_queue, posID)
        # start imaging
        self.controller.imagingActive = True
        self.controller.queRun = threading.Thread(target=self.controller.run_step_from_queue)
        self.controller.queRun.daemon = True
        self.controller.queRun.start()

    def stop_imaging(self):
        for posID in self.posTimers:
            self.posTimers[posID].stop()
        self.controller.imagingActive = False
