
import tkinter as tk
from tkinter import ttk
import numpy as np
# from scipy import ndimage
from skimage import io, transform
import matplotlib

from guis.MacroWindow import MacroWindow
from guis.PositionsPage import PositionsPage
from guis.StartPage import StartPage
from guis.SettingsPage import SettingsPage
from guis.TimelinePage import TimelinePage
# from utilities.DraggableCircle import DraggableCircle
from io_communication.GetCommands import GetCommands
from io_communication.SendCommands import SendCommands
from io_communication.file_listeners import InstructionThread
from utilities.helper_functions import fitFigToCanvas, initializeInitDirectory
from utilities.math_helpers import floatOrZero, floatOrNone, round_math, focusMeasure, computeDrift

matplotlib.use("TkAgg")
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
# import matplotlib.animation as animation
from matplotlib import style
# import matplotlib.gridspec as gridspec
from matplotlib import patches
import datetime as dt
# import matplotlib.pyplot as plt
# import matplotlib.font_manager as font_manager
# import matplotlib.dates
# import matplotlib.colorbar as colorbar
# from matplotlib.dates import MONTHLY, DateFormatter, rrulewrapper, RRuleLocator
import pickle
import os
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from queue import Queue
# import cv2
from PIL import Image, ImageTk, ImageOps, ImageMath
# import math
import inspect
# import timeit
# import sys

class PositionTimer(object):
    def __init__(self, controller, steps, function, *args, **kwargs):
        self.controller = controller
        self._timer = None
        self.steps = steps
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.stepCount = 0

        self.runTimes = []
        for step in self.steps:
            self.runTimes.append(step['startTime'])

        self.start()

    def _run(self, stepCount):
        self.is_running = False
        self.start()  # starts next timer countdown before running function
        self.function(self.steps[stepCount], *self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            if self.stepCount >= len(self.runTimes):
                return
            if self.stepCount == 0:
                prevTime = 0
            else:
                prevTime = self.runTimes[self.stepCount - 1]
            interval = self.runTimes[self.stepCount] - prevTime
            stepCount = self.stepCount
            self.stepCount += 1
            # for now, interval is store in minutes. probably a good idea to change it to seconds.
            interval = interval * 60
            printStatus('\nTimer Interval = {0}'.format(interval))
            self._timer = threading.Timer(interval, self._run, args=[stepCount])
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
