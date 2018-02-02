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


class PositionsPage(ttk.Frame):
    name = 'Positions'

    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.bind("<Visibility>", self.on_visibility)
        self.controller = controller
        frame_forButtons = ttk.Frame(self)
        frame_forButtons.grid(column=0, row=0, sticky='nw')
        frame_forZoom = ttk.Frame(self)
        frame_forZoom.grid(column=1, row=3, sticky='ew', padx=10, pady=10)
        frame_forGraphics = ttk.Frame(self)
        frame_forGraphics.grid(column=1, row=0, sticky='nsew')
        button_addPosition = ttk.Button(frame_forButtons, text="Add current position",
                                        command=lambda: controller.add_position(self))
        button_addPosition.grid(row=0, column=0, padx=10, pady=10, sticky='wn')
        button_clearPositions = ttk.Button(frame_forButtons, text="Clear All Positions",
                                           command=lambda: controller.clear_positions(self))
        button_clearPositions.grid(row=1, column=0, padx=10,
                                   pady=10, sticky='wn')
        button_cellView = ttk.Button(frame_forButtons, text="Macro View",
                                     command=lambda: controller.show_macro_view_window())
        button_cellView.grid(row=2, column=0, padx=10,
                             pady=10, sticky='wn')

        label_imagingZoom = tk.Label(frame_forZoom, text="Imaging Zoom", font=self.controller.get_app_param('large_font'))
        label_imagingZoom.grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        self.imagingZoom = tk.StringVar(self)
        self.imagingZoom.set(self.controller.settings['imagingZoom'])
        self.imagingZoom.trace('w', lambda a, b, c, source=self.imagingZoom, name='imagingZoom':
        self.controller.update_settings(name, source, a, b, c))

        entry_imagingZoom = ttk.Entry(frame_forZoom, textvariable=self.imagingZoom)
        entry_imagingZoom.grid(row=0, column=1, padx=10, pady=10, sticky='nw')
        label_refZoom = tk.Label(frame_forZoom, text="Reference Zoom", font=self.controller.get_app_param('large_font'))
        label_refZoom.grid(row=0, column=2, sticky='nw', padx=10, pady=10)
        self.refZoom = tk.StringVar(self)
        self.refZoom.set(self.controller.settings['referenceZoom'])
        self.refZoom.trace('w', lambda a, b, c, source=self.refZoom, name='referenceZoom':
        self.controller.update_settings(name, source, a, b, c))
        entry_refZoom = ttk.Entry(frame_forZoom, textvariable=self.refZoom)
        entry_refZoom.grid(row=0, column=3, padx=10, pady=10, sticky='nw')

        label_imagingSlices = tk.Label(frame_forZoom, text="Imaging Slices", font=self.controller.get_app_param('large_font'))
        label_imagingSlices.grid(row=1, column=0, sticky='nw', padx=10, pady=10)
        self.imagingSlices = tk.StringVar(self)
        self.imagingSlices.set(self.controller.settings['imagingSlices'])
        self.imagingSlices.trace('w', lambda a, b, c, source=self.imagingSlices, name='imagingSlices':
        self.controller.update_settings(name, source, a, b, c))
        entry_imagingSlices = ttk.Entry(frame_forZoom, textvariable=self.imagingSlices)
        entry_imagingSlices.grid(row=1, column=1, padx=10, pady=10, sticky='nw')
        label_refSlices = tk.Label(frame_forZoom, text="Reference Slices", font=self.controller.get_app_param('large_font'))
        label_refSlices.grid(row=1, column=2, sticky='nw', padx=10, pady=10)
        self.refSlices = tk.StringVar(self)
        self.refSlices.set(self.controller.settings['referenceSlices'])
        self.refSlices.trace('w', lambda a, b, c, source=self.refSlices, name='referenceSlices':
        self.controller.update_settings(name, source, a, b, c))
        entry_refSlices = ttk.Entry(frame_forZoom, textvariable=self.refSlices)
        entry_refSlices.grid(row=1, column=3, padx=10, pady=10, sticky='nw')

        f_positions = Figure(figsize=(3, 3), dpi=controller.get_app_param('fig_dpi'))
        f_positions.subplots_adjust(left=0, right=1, bottom=0, top=1)
        f_positions.set_tight_layout(True)

        # treeview example given at http://knowpapa.com/ttk-treeview/
        positionsTableFrame = ttk.Frame(frame_forGraphics)
        positionsTableFrame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        self.createPositionsTable(positionsTableFrame)

        # create canvas for previewing reference images
        f1 = Figure(figsize=(4, 2), dpi=controller.get_app_param('fig_dpi'))
        f1.subplots_adjust(left=0, right=1, bottom=0, top=1, wspace=0.02, hspace=0)
        canvas_previewRefImages = FigureCanvasTkAgg(f1, frame_forGraphics)
        canvas_previewRefImages.get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                                       highlightbackground='gray')
        canvas_previewRefImages.show()
        canvas_previewRefImages.get_tk_widget().grid(row=1, column=0, padx=10, sticky='nsew')
        a1 = []
        self.canvas_previewRefImages = canvas_previewRefImages
        for i in range(2):
            a1.append(f1.add_subplot(1, 2, i + 1))
        controller.refImgAx = a1
        controller.refImgFig = f1
        # relative positions figure
        f_positions.set_size_inches(4, 4)
        canvas_positions = FigureCanvasTkAgg(f_positions, frame_forGraphics)
        canvas_positions.show()
        canvas_positions.get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                                highlightbackground='gray')
        canvas_positions.get_tk_widget().grid(row=0, column=2, rowspan=2, padx=10, pady=10, sticky='nsew')
        a2 = f_positions.add_subplot(1, 1, 1)
        cAx, kw = colorbar.make_axes_gridspec(a2)
        self.canvas_positions = canvas_positions
        self.positionPreviewAxis = a2
        self.colorbarAxis = cAx
        self.previewPositionLocations()

    def createPositionsTable(self, container):
        tree = ttk.Treeview(container)
        tree["columns"] = ("x", "y", "z")
        tree.column("#0", width=300)
        tree.column("x", width=30)
        tree.column("y", width=30)
        tree.column("z", width=50)
        tree.heading("x", text="X")
        tree.heading("y", text="Y")
        tree.heading("z", text="Z")
        tree.bind("<Button-3>", self.onTreeRightClick)
        tree.bind("<<TreeviewSelect>>", self.onTreeSelect)
        tree.grid(row=0, column=0, sticky='nsew')
        scroll = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        scroll.grid(row=0, column=1, pady=10, sticky='nsw')
        tree.configure(yscrollcommand=scroll.set)
        self.tree = tree

    def previewPositionLocations(self):
        positions = self.controller.positions
        ax = self.positionPreviewAxis
        cAx = self.colorbarAxis
        w = 8
        h = 8
        ax.clear()
        cAx.clear()
        X = np.array([])
        Y = np.array([])
        Z = np.array([])
        for posID in positions:
            X = np.append(X, positions[posID]['x'])
            Y = np.append(Y, positions[posID]['y'])
            Z = np.append(Z, positions[posID]['z'])

        if len(positions) > 0:
            vmin = Z.min() - 1
            vmax = Z.max() + 1
        else:
            vmin = -100
            vmax = 100

        posLabels = list(positions.keys())
        cmap = matplotlib.cm.jet
        norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
        for x, y, z, p in zip(X, Y, Z, posLabels):
            ax.add_patch(patches.Rectangle(xy=(x, y), width=w, height=h,
                                           facecolor=cmap(norm(z))))
            ax.annotate(str(p), xy=(x, y), xytext=(x + w, y + h))
        cb1 = colorbar.ColorbarBase(ax=cAx, cmap=cmap, norm=norm)
        cb1.set_label('Z (µm)')
        ax.set_ylabel('Y (µm)')
        ax.set_xlabel('X (µm)')
        ax.axis('equal')
        cb1.ax.yaxis.label.set_size(8)
        ax.xaxis.label.set_size(8)
        ax.yaxis.label.set_size(8)
        ax.relim()
        xlim0, xlim1 = ax.get_xlim()
        ylim0, ylim1 = ax.get_ylim()
        clim0, clim1 = cb1.ax.get_ylim()
        ax.xaxis.set_ticks([int(xlim0), int(xlim1)])
        ax.yaxis.set_ticks([int(ylim0), int(ylim1)])
        cb1.ax.yaxis.set_ticks([int(clim0), int(clim1)])
        ax.autoscale_view()
        self.canvas_positions.draw_idle()

    def on_visibility(self, event):
        fitFigToCanvas(f_positions, self.canvas_positions)
        self.redrawPositionTable()
        self.canvas_previewRefImages.draw_idle()

    def onTreeRightClick(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            # mouse over item
            self.tree.selection_set(iid)
        for item in self.tree.selection():
            item_text = self.tree.item(item, "text")
            print(item_text)
        if len(self.tree.selection()) == 0:
            return
        self.popup = tk.Menu(self, tearoff=0)
        posID = int(item_text.split()[1])
        self.popup.add_command(label="Update XYZ", command=lambda: self.controller.update_position(posID))
        self.popup.add_command(label="Delete", command=lambda: self.controller.delete_positions(posID))
        self.popup.post(event.x_root, event.y_root)

    def onTreeSelect(self, event):
        for item in self.tree.selection():
            item_text = self.tree.item(item, "text")
            posID = int(item_text.split()[1])
        self.drawRefImages(posID)
        self.selectPositionInGraph(posID)

    def selectPositionInGraph(self, posID):
        positions = self.controller.positions
        ax = self.positionPreviewAxis
        x = positions[posID]['x']
        y = positions[posID]['y']
        arrowprops = dict(facecolor='black')
        arrow = ax.annotate("", xy=(x, y), xytext=(x - 10, y - 10), arrowprops=arrowprops)
        try:
            self.selectionArrow.remove()
        except:
            pass
        self.selectionArrow = arrow
        self.canvas_positions.draw_idle()

    def redrawPositionTable(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for posID in self.controller.positions:
            x = self.controller.positions[posID]['x']
            y = self.controller.positions[posID]['y']
            z = self.controller.positions[posID]['z']
            self.tree.insert("", posID, text="Position {0}".format(posID),
                             values=(x, y, z))
        self.previewPositionLocations()
        self.canvas_previewRefImages.draw_idle()

    def drawRefImages(self, posID):
        refs = [self.controller.positions[posID]['refImg'], self.controller.positions[posID]['refImgZoomout']]
        for ax, r in zip(self.controller.refImgAx, refs):
            ax.clear()
            ax.axis('off')
            ax.imshow(r)
        self.drawROI(posID, self.controller.refImgAx[0])
        self.canvas_previewRefImages.draw_idle()

    def drawROI(self, posID, ax):
        if self.controller.frames[SettingsPage].uncaging_roi_toggle:
            axWidth = abs(np.diff(ax.get_xlim()).item())
            x, y = self.controller.positions[posID]['roi_position']
            circ = patches.Circle((x, y), radius=axWidth / 20, fill=False, linewidth=axWidth / 20, edgecolor='r')
            ax.add_patch(circ)
            dc = DraggableCircle(self, self.controller.positions[posID], circ)
            dc.connect()
            self.draggable_circle = dc
