# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 11:01:40 2018

@author: mikeu
"""

# draggable Circle with the animation blit techniques; see
# http://www.scipy.org/Cookbook/Matplotlib/Animations
import numpy as np


# import matplotlib.pyplot as plt
class DraggableShape:
    lock = None  # only one can be animated at a time

    def __init__(self, position, shape):
        self.position = position
        self.shape = shape
        self.press = None
        self.background = None

    def connect(self):
        'connect to all the events we need'

        self.cidpress = self.shape.figure.canvas.mpl_connect(
            'button_press_event', self.on_press)
        self.cidrelease = self.shape.figure.canvas.mpl_connect(
            'button_release_event', self.on_release)
        self.cidmotion = self.shape.figure.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)

    def on_press(self, event):
        'on button press we will see if the mouse is over us and store some data'
        if event.inaxes != self.shape.axes: return
        if DraggableShape.lock is not None: return
        contains, attrd = self.shape.contains(event)
        if not contains: return
        x0, y0 = self.shape.center
        self.press = x0, y0, event.xdata, event.ydata
        DraggableShape.lock = self

        # draw everything but the selected Rectangle and stores the pixel buffer
        canvas = self.shape.figure.canvas
        axes = self.shape.axes
        self.shape.set_animated(True)
        canvas.draw()
        self.background = canvas.copy_from_bbox(self.shape.axes.bbox)

        # now redraw just the rectangle
        axes.draw_artist(self.shape)

        # and blit just the redrawn area
        canvas.blit(axes.bbox)

    def on_motion(self, event):
        'on motion we will move the circ if the mouse is over us'
        if DraggableShape.lock is not self:
            return
        if event.inaxes != self.shape.axes: return
        x0, y0, xpress, ypress = self.press
        dx = event.xdata - xpress
        dy = event.ydata - ypress

        new_x, new_y = x0 + dx, y0 + dy
        self.shape.center = (new_x, new_y)

        canvas = self.shape.figure.canvas
        axes = self.shape.axes
        # restore the background region
        canvas.restore_region(self.background)

        # redraw just the current Circle
        axes.draw_artist(self.shape)

        # blit just the redrawn area
        canvas.blit(axes.bbox)

    def on_release(self, event):
        'on release we reset the press data'
        if DraggableShape.lock is not self:
            return

        self.press = None
        DraggableShape.lock = None

        # turn off the circ animation property and reset the background
        self.shape.set_animated(False)
        self.background = None
        self.position.set_roi_x_y(np.array(self.shape.center))
        # redraw the full figure
        self.shape.figure.canvas.draw_idle()

    def disconnect(self):
        'disconnect all the stored connection ids'
        self.shape.figure.canvas.mpl_disconnect(self.cidpress)
        self.shape.figure.canvas.mpl_disconnect(self.cidrelease)
        self.shape.figure.canvas.mpl_disconnect(self.cidmotion)