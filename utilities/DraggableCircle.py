# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 11:01:40 2018

@author: mikeu
"""

# draggable Circle with the animation blit techniques; see
# http://www.scipy.org/Cookbook/Matplotlib/Animations
import numpy as np
#import matplotlib.pyplot as plt


class DraggableCircle:
    lock = None  # only one can be animated at a time
    def __init__(self, master, position, circ):
        self.master = master
        self.position = position
        self.circ = circ
        self.press = None
        self.background = None

    def connect(self):
        'connect to all the events we need'

        self.cidpress = self.circ.figure.canvas.mpl_connect(
            'button_press_event', self.on_press)
        self.cidrelease = self.circ.figure.canvas.mpl_connect(
            'button_release_event', self.on_release)
        self.cidmotion = self.circ.figure.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)

    def on_press(self, event):
        'on button press we will see if the mouse is over us and store some data'
        if event.inaxes != self.circ.axes: return
        if DraggableCircle.lock is not None: return
        contains, attrd = self.circ.contains(event)
        if not contains: return
#        print('event contains', self.circ.center)
        x0, y0 = self.circ.center
        self.press = x0, y0, event.xdata, event.ydata
        DraggableCircle.lock = self

        # draw everything but the selected Circle and store the pixel buffer
        canvas = self.circ.figure.canvas
        axes = self.circ.axes
        self.circ.set_animated(True)
        canvas.draw()
        self.background = canvas.copy_from_bbox(self.circ.axes.bbox)

        # now redraw just the circangle
        axes.draw_artist(self.circ)

        # and blit just the redrawn area
        canvas.blit(axes.bbox)

    def on_motion(self, event):
        'on motion we will move the circ if the mouse is over us'
        if DraggableCircle.lock is not self:
            return
        if event.inaxes != self.circ.axes: return
        x0, y0, xpress, ypress = self.press
        dx = event.xdata - xpress
        dy = event.ydata - ypress
        
        new_x,new_y = x0+dx, y0+dy
        self.circ.center = (new_x,new_y)
        
        canvas = self.circ.figure.canvas
        axes = self.circ.axes
        # restore the background region
        canvas.restore_region(self.background)

        # redraw just the current Circle
        axes.draw_artist(self.circ)

        # blit just the redrawn area
        canvas.blit(axes.bbox)

    def on_release(self, event):
        'on release we reset the press data'
        if DraggableCircle.lock is not self:
            return

        self.press = None
        DraggableCircle.lock = None

        # turn off the circ animation property and reset the background
        self.circ.set_animated(False)
        self.background = None
        self.position.set_roi_x_y(np.array(self.circ.center))
        self.master.controller.backup_positions()
        # redraw the full figure
        self.circ.figure.canvas.draw_idle()

    def disconnect(self):
        'disconnect all the stored connection ids'
        self.circ.figure.canvas.mpl_disconnect(self.cidpress)
        self.circ.figure.canvas.mpl_disconnect(self.cidrelease)
        self.circ.figure.canvas.mpl_disconnect(self.cidmotion)

#fig = plt.figure()
#ax = fig.add_subplot(111)
#rects = ax.bar(range(10), 20*np.random.rand(10))
#drs = []
#for rect in rects:
#    dr = DraggableRectangle(rect)
#    dr.connect()
#    drs.append(dr)
#
#plt.show()