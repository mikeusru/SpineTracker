import tkinter as tk
from tkinter import ttk
import numpy as np
from scipy import ndimage
from skimage import io, transform
import matplotlib

from utilities.DraggableCircle import DraggableCircle
from utilities.helper_functions import fitFigToCanvas, initializeInitDirectory
from utilities.math_helpers import floatOrZero, floatOrNone, round_math, focusMeasure, computeDrift

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
import matplotlib.gridspec as gridspec
from matplotlib import patches
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import matplotlib.dates
import matplotlib.colorbar as colorbar
from matplotlib.dates import MONTHLY, DateFormatter, rrulewrapper, RRuleLocator
import pickle
import os
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from queue import Queue
import cv2
from PIL import Image, ImageTk, ImageOps, ImageMath
import math
import inspect
import timeit
import sys

class SettingsPage(ttk.Frame):
    name = 'Settings'

    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Total Image Channels", font=LARGE_FONT)
        label.grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        self.totalChannelsVar = tk.StringVar(self)
        entry_totalChannels = ttk.Entry(self, textvariable=self.totalChannelsVar)
        entry_totalChannels.grid(row=0, column=1, padx=10, pady=10, sticky='nw')
        label2 = tk.Label(self, text="Drift Correction Channel", font=LARGE_FONT)
        label2.grid(row=1, column=0, sticky='nw', padx=10, pady=10)
        self.driftCorrectionChannelVar = tk.StringVar(self)
        entry_driftChannel = ttk.Entry(self, textvariable=self.driftCorrectionChannelVar)
        entry_driftChannel.grid(row=1, column=1, padx=10, pady=10, sticky='nw')
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
        self.setDefaultSettings()

    def setDefaultSettings(self):
        try:
            self.totalChannelsVar.set(self.controller.settings['totalChannels'])
        except:
            pass
        try:
            self.driftCorrectionChannelVar.set(self.controller.settings['driftCorrectionChannel'])
        except:
            pass
        self.xy_mode.set("Galvo")
        self.uncaging_roi_toggle.set(True)

    def toggle_xy_mode(self, *args):
        mode = self.xy_mode.get()
        printStatus(mode)
        if mode == 'Galvo':
            self.controller.parkXYmotor = True
        else:
            self.controller.parkXYmotor = False
