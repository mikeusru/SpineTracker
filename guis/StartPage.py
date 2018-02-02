import tkinter as tk
from tkinter import ttk

import matplotlib

from flow.PositionTimer import PositionTimer
from guis.PositionsPage import PositionsPage
from utilities.helper_functions import fitFigToCanvas

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading


class StartPage(ttk.Frame):
    name = 'Main'

    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.bind("<Visibility>", self.on_visibility)
        frame_leftButtons = ttk.Frame(self)
        frame_leftButtons.grid(row=0, column=0, rowspan=2, sticky='nw')
        button = ttk.Button(frame_leftButtons, text="Load Test Image", command=
        lambda: controller.load_test_image(self))
        button.grid(row=0, column=0, padx=10, pady=10, sticky='nw')
        button1 = ttk.Button(frame_leftButtons, text="Load Test Ref Image", command=
        lambda: controller.load_test_ref_image(self))
        button1.grid(row=1, column=0, padx=10, pady=10, sticky='nw')
        button2 = ttk.Button(frame_leftButtons, text="Run Drift Correction", command=
        lambda: controller.run_xyz_drift_correction(1))
        button2.grid(row=2, column=0, padx=10, pady=10, sticky='nw')
        button_start = ttk.Button(frame_leftButtons, text="Start Imaging", command=
        lambda: self.start_imaging())
        button_start.grid(row=3, column=0, padx=10, pady=10, sticky='nw')
        button_end = ttk.Button(frame_leftButtons, text="Stop Imaging", command=
        lambda: self.stopImaging())
        button_end.grid(row=4, column=0, padx=10, pady=10, sticky='nw')
        #        button_listen = ttk.Button(frame_leftButtons,text = "Listen For Instructions", command =
        #                                  lambda:controller.listenToInstructionsFile())
        #        button_listen.grid(row = 5, column = 0, padx = 10, pady = 10, sticky = 'nw')

        driftLabel = tk.Label(self, text="drift placeholder",
                              font=controller.get_app_param('large_font'))
        driftLabel.grid(row=0, column=1, padx=10, pady=10, sticky='nw')
        frame_forCanvases = ttk.Frame(self)
        frame_forCanvases.grid(row=1, column=1, columnspan=2, rowspan=2)
        f = Figure(figsize=(5, 2), dpi=controller.get_app_param('fig_dpi'))
        #        f.set_tight_layout(True)
        f.subplots_adjust(left=0, right=1, bottom=0, wspace=0.02, hspace=0)
        a = [f.add_subplot(1, 1, 1)]
        self.ax_af_image = a
        self.fig_af_image = f
        canvas_af = FigureCanvasTkAgg(f, frame_forCanvases)
        canvas_af.show()
        canvas_af.get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                         highlightbackground='gray')
        canvas_af.get_tk_widget().grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        self.driftLabel = driftLabel
        canvas_timeline = FigureCanvasTkAgg(controller.f_timeline, frame_forCanvases)
        canvas_timeline.show()
        canvas_timeline.get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                               highlightbackground='gray')
        canvas_timeline.get_tk_widget().grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        canvas_positions = FigureCanvasTkAgg(controller.f_positions, frame_forCanvases)
        canvas_positions.show()
        canvas_positions.get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                                highlightbackground='gray')
        canvas_positions.get_tk_widget().grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky='nsew')
        self.canvas = dict(canvas_timeline=canvas_timeline, canvas_positions=canvas_positions, canvas_af=canvas_af)

    def on_visibility(self, event):
        fitFigToCanvas(self.controller.f_timeline, self.canvas['canvas_timeline'], self.controller.get_app_param('fig_dpi'))
        fitFigToCanvas(self.controller.f_positions, self.canvas['canvas_positions'], self.controller.get_app_param('fig_dpi'))
        for key in self.canvas:
            self.canvas[key].draw_idle()

    def start_imaging(self):
        # get scan angle conversion properties
        self.controller.get_scan_props()
        # this probably needs to move somewhere else later
        self.controller.set_zoom(float(self.controller.frames[PositionsPage].imagingZoom.get()))
        # set up timers
        self.posTimers = {}
        with self.controller.timerStepsQueue.mutex:
            self.controller.timerStepsQueue.queue.clear()
        individualSteps = self.controller.individualTimelineSteps
        for posID in individualSteps:
            self.posTimers[posID] = PositionTimer(self.controller, individualSteps[posID],
                                                  self.controller.add_step_to_queue, posID)
        # start imaging
        self.controller.imagingActive = True
        self.controller.queRun = threading.Thread(target=self.controller.run_step_from_queue)
        self.controller.queRun.daemon = True
        self.controller.queRun.start()

    def stopImaging(self):
        for posID in self.posTimers:
            self.posTimers[posID].stop()
        self.controller.imagingActive = False
