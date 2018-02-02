
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

class InstructionThread(object):
    def __init__(self, controller, path, filename, function, *args, **kwargs):
        self.controller = controller
        self.path = path
        self.filename = filename
        self.function = function
        self.observer = Observer()
        self.args = args
        self.kwargs = kwargs
        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True

    def start(self):
        self.thread.start()

    def run(self):
        """Method that runs forever"""
        self.event_handler = InstructionHandler(self.controller, self.path, self.filename, self.function, self.args,
                                                self.kwargs)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, path=self.path, recursive=False)
        self.observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.observer.stop()
        self.observer.join()


class InstructionHandler(FileSystemEventHandler):
    def __init__(self, controller, path, filename, function, *args, **kwargs):
        self.controller = controller
        self.path = path
        self.filename = filename
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(self.filename):
            self.function(self.args)