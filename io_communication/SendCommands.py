
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

class SendCommands(object):
    def __init__(self, controller, filepath, *args, **kwargs):
        self.controller = controller
        self.filepath = filepath
        self.args = args
        self.kwargs = kwargs
        if not os.path.isfile(filepath):
            open(filepath, 'a').close()

    def moveStage(self, x, y, z):
        self.writeCommand('moveXYZ', x, y, z)

    def grabOneStack(self):
        self.writeCommand('grabOneStack')

    def setZoom(self, zoom):
        self.writeCommand('setZoom', zoom)

    def doUncaging(self, roi_x, roi_y):
        self.writeCommand('runUncaging', roi_x, roi_y)

    def getFOVsize(self):
        self.writeCommand('getFOV_xy')

    def getScanAngleXY(self):
        self.writeCommand('getScanAngleXY')

    def getScanAngleMultiplier(self):
        self.writeCommand('getScanAngleMultiplier')

    def getScanAngleRangeReference(self):
        self.writeCommand('getScanAngleRangeReference')

    def getCurrentPosition(self):
        self.writeCommand('getCurrentPosition', 'xyz')

    def setScanShift(self, scanShiftFast, scanShiftSlow):
        self.writeCommand('setScanAngleXY', scanShiftFast, scanShiftSlow)

    def setZSliceNum(self, z_slice_num):
        self.writeCommand('setZSliceNum', z_slice_num)

    def writeCommand(self, *args):
        command = ",".join([str(x) for x in args])
        printStatus('\nWriting Command {0}\n'.format(command))
        with open(self.filepath, "a") as f:
            f.write('\n' + command)
