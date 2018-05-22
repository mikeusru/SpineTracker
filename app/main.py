# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 14:36:57 2017

@author: smirnovm
"""
import copy
import datetime as dt
import inspect
import os
import pickle
from queue import Queue

import matplotlib
import numpy as np
import sys
from matplotlib import patches
from matplotlib import style
from matplotlib.figure import Figure
from skimage import io, transform

from app.inherited.InputOutputInterface import InputOutputInterface
from flow.TimelineStep import TimelineStep
from guis.MacroWindow import MacroWindow
from guis.PositionsPage import PositionsPage
from guis.SettingsPage import SettingsPage
from guis.StartPage import StartPage
from guis.TimelinePage import TimelinePage
from io_communication.file_listeners import InstructionThread
from utilities.helper_functions import initialize_init_directory
from utilities.math_helpers import focus_measure, compute_drift

matplotlib.use("TkAgg")
style.use("ggplot")


class SpineTracker(InputOutputInterface):

    def __init__(self, *args, **kwargs):
        super(SpineTracker, self).__init__(*args, **kwargs)

        self.timeline_steps = []

        # set properties for main window
        self.protocol("WM_DELETE_WINDOW", self.on_exit)
        # define container for what's in the window

        self.initialize_timeline_steps()
        self.initialize_positions()
        self.frames = {}
        self.windows = {}
        self.stepRunning = False
        self.instructions_in_queue = Queue()
        self.timerStepsQueue = Queue()

        # Shared Figures
        self.shared_figs = SharedFigs(self.get_app_param('fig_dpi'))

        # initialize instructions listener
        path, filename = os.path.split(self.inputFile)
        with self.instructions_in_queue.mutex:
            self.instructions_in_queue.queue.clear()
        self.ins_thread = InstructionThread(self, path, filename, self.getCommands.read_new_instructions)
        self.ins_thread.start()

        self.acq['center_xyz'] = np.array((0, 0, 0))
        initialize_init_directory(self.get_app_param('initDirectory'))
        # create/refresh log file
        self.log_file = open('log.txt', 'w')

        # define frames (windows) available which will appear in main window
        for F in (StartPage, SettingsPage, PositionsPage, TimelinePage):
            frame = F(self.container, self)
            self.frames[F] = frame
            self.container.add(frame, text=F.name)

        self.current_pos_id = 1

    def show_macro_view_window(self):
        self.windows[MacroWindow] = MacroWindow(self)

    def on_exit(self):
        print('quitting')
        self.ins_thread.stop()
        print('Instruction listener closed')
        self.log_file.close()
        self.destroy()
        print('goodbye')

    def start_expt_log(self):
        file_path = self.get_settings('experiment_log_file')
        open(file_path, 'a').close()

    def write_to_log(self, line):
        file_path = self.get_settings('experiment_log_file')
        with open(file_path, "a") as f:
            f.write(line + '\n')

    def initialize_timeline_steps(self):
        file_name = self.get_app_param('initDirectory') + 'timeline_steps.p'
        if os.path.isfile(file_name):
            self.timeline_steps = pickle.load(open(file_name, 'rb'))

    def load_test_image(self, event):  # for testing purposes only
        image = io.imread("../testing/test_image.tif")
        image = image[np.arange(0, len(image), 2)]
        self.acq['imageStack'] = image
        self.create_figure_for_af_images()

    def load_acquired_image(self, update_figure=True, get_macro=False):
        image = io.imread(self.image_file_path)
        total_chan = int(self.gui_vars['total_channels_string_var'].get())
        drift_chan = int(self.gui_vars['drift_correction_channel_string_var'].get())
        image = image[np.arange(drift_chan - 1, len(image), total_chan)]
        self.acq['imageStack'] = image
        if get_macro:
            self.acq['macro_image'] = image
        if update_figure:
            self.create_figure_for_af_images()

    def load_test_ref_image(self):  # for testing purposes only
        imgref = io.imread("../testing/test_refimg.tif")
        #        self.acq['imgref'] = imgref
        self.acq['imgref_imaging'] = imgref
        self.acq['imgref_ref'] = imgref

    def run_xyz_drift_correction(self, pos_id=None, ref_zoom=None):
        if 'imageStack' not in self.acq:
            return
        if pos_id is None:
            pos_id = self.current_pos_id
        shape = self.acq['imageStack'][0].shape
        self.acq['imgref_imaging'] = transform.resize(self.positions[pos_id]['ref_img'], shape)
        self.acq['imgref_ref'] = transform.resize(self.positions[pos_id]['ref_img_zoomout'], shape)
        self.calc_focus()
        self.calc_drift(ref_zoom)
        # x, y, z = [self.positions[pos_id][key] for key in ['x', 'y', 'z']]
        shiftx, shifty = self.acq['shiftxy']
        shiftz = self.acq['shiftz']
        self.positions[pos_id]['x'] -= shiftx
        self.positions[pos_id]['y'] += shifty
        self.positions[pos_id]['z'] += shiftz
        self.positions[pos_id]['xyzShift'] = self.positions[pos_id]['xyzShift'] + np.array([shiftx, shifty, shiftz])
        self.frames[StartPage].gui['drift_label'].configure(
            text='Detected drift of {0:.1f}µm in x and {1:.1f}µm in y'.format(shiftx.item(), shifty.item()))
        self.show_new_images(pos_id=pos_id)
        self.backup_positions()

    def show_new_images(self, pos_id=None):
        image = self.acq['imageStack']
        i = 0
        a = self.frames[StartPage].gui['axes_af_images']
        # show images
        for im in image:
            a[i].clear()
            a[i].imshow(im)
            a[i].axis('equal')
            a[i].axis('off')
            i += 1
        # show best focused image
        max_ind = self.acq['FMlist'].argmax().item()
        siz = image[0].shape
        rect = patches.Rectangle((0, 0), siz[0], siz[1], fill=False, linewidth=5, edgecolor='r')
        a[max_ind].add_patch(rect)
        # add arrow to show shift in x,y
        center = np.array([siz[0] / 2, siz[1] / 2])
        shiftx, shifty = self.acq['shiftxy_pixels']['shiftx'], self.acq['shiftxy_pixels']['shifty']
        arrow = patches.Arrow(center[1] - shiftx, center[0] - shifty, shiftx, shifty, width=10, color='r')
        a[max_ind].add_patch(arrow)
        if pos_id is not None:
            self.frames[PositionsPage].select_position_in_graph(pos_id)
        self.frames[StartPage].gui['canvas_positions'].draw_idle()
        self.frames[StartPage].gui['canvas_af'].draw_idle()

    def calc_focus(self):
        image = self.acq['imageStack']
        fm = np.array([])
        for im in image:
            fm = np.append(fm, (focus_measure(im)))
        self.acq['shiftz'] = fm.argmax().item() - np.floor(
            len(image) / 2)
        self.acq['FMlist'] = fm

    def calc_drift(self, ref_zoom=None):
        image = np.max(self.acq['imageStack'], 0)
        zoom = np.float(self.get_acq_var('current_zoom'))
        fov_x_y = self.settings['fov_x_y']
        if ref_zoom is None:
            ref_zoom = (self.acq['current_zoom'] == float(self.get_settings('reference_zoom')))
        if ref_zoom:
            imgref = self.acq['imgref_ref']
        else:
            imgref = self.acq['imgref_imaging']
        self.acq['shiftxy_pixels'] = compute_drift(imgref, image)
        shiftx, shifty = np.array(
            [self.acq['shiftxy_pixels']['shiftx'], self.acq['shiftxy_pixels']['shifty']]) / image.shape * fov_x_y / zoom
        self.acq['shiftxy'] = (shiftx, shifty)

    def create_figure_for_af_images(self):
        if 'imageStack' not in self.acq:
            return
        image = self.acq['imageStack']
        subplot_length = len(image)
        f = self.frames[StartPage].gui['figure_af_images']
        a = self.frames[StartPage].gui['axes_af_images']
        for ax in a.copy():
            a.remove(ax)
            f.delaxes(ax)
        for i in range(subplot_length):
            a.append(f.add_subplot(1, subplot_length, i + 1))

    def add_timeline_step(self, timeline_step):
        index = timeline_step.get('index')
        if index is None:
            self.timeline_steps.append(timeline_step)
        else:
            self.timeline_steps.insert(index, timeline_step)

        self.frames[TimelinePage].draw_timeline_steps()

    def add_step_to_queue(self, step, pos_id):
        single_step = copy.copy(step)  # .copy() returns dict, not TimelineStep object
        single_step['pos_id'] = pos_id
        self.timerStepsQueue.put(single_step)

    def run_step_from_queue(self):
        while self.imagingActive:
            # update() function on the GUI is necessary to keep it active
            self.update()
            if self.stepRunning:  # make sure something isn't already running
                continue
            if not self.timerStepsQueue.empty():
                single_step = self.timerStepsQueue.get()
            else:
                continue
            self.stepRunning = True
            pos_id = single_step.get('pos_id')
            if single_step.get('exclusive'):
                ex = 'Exclusive'
            else:
                ex = 'Non-Exclusive'
            print('{0} {1} Timer {2} running at {3}:{4}:{5} '.format(ex, single_step['imaging_or_uncaging'], pos_id,
                                                              dt.datetime.now().hour, dt.datetime.now().minute,
                                                              dt.datetime.now().second))

            # this should actually be set once data from position is received, because drift/af calculation will be
            # done after that
            self.current_pos_id = pos_id
            # we're already in a thread so maybe don't need another one here
            if single_step['imaging_or_uncaging'] == 'Image':
                self.image_new_position(single_step)
            elif single_step['imaging_or_uncaging'] == 'Uncage':
                self.uncage_new_position(single_step)

    def image_new_position(self, single_step=None, pos_id=None, ref_zoom=None):
        if pos_id is None:
            pos_id = single_step.get('pos_id')
        x, y, z = [self.positions[pos_id][key] for key in ['x', 'y', 'z']]
        self.move_stage(x, y, z)
        self.grab_stack()
        self.write_to_log('Position {}: {}'.format(pos_id,  self.image_file_path))
        if single_step is not None:
            self.stepRunning = False
        self.load_acquired_image()
        self.run_xyz_drift_correction(pos_id, ref_zoom=ref_zoom)

    def uncage_new_position(self, step=None, pos_id=None):
        if pos_id is None:
            pos_id = step.get('pos_id')
        x, y, z = [self.positions[pos_id][key] for key in ['x', 'y', 'z']]
        roi_x, roi_y = self.positions[pos_id]['roi_position']
        self.move_stage(x, y, z)
        self.write_to_log('Position {0}: Uncaging at {1}:{2}:{3}'.format(pos_id, dt.datetime.now().hour,
                                                                         dt.datetime.now().minute,
                                                                         dt.datetime.now().second))
        self.uncage(roi_x, roi_y)
        if step is not None:
            self.stepRunning = False

    def print_status(self, following_string):
        if self.app_params['verbose']:
            # following_string is a string to add after the function. something like Started or Finished
            string = '\nFunction {0} {1}\n'.format(inspect.stack()[1][3], following_string)
            print(string)
            self.log_file.write(string)

    def stagger_string_var_callback(self, *args):
        # Callback to the StringVar
        self.frames[TimelinePage].create_timeline_chart()

    def image_or_uncage_string_var_callback(self, *args):
        # Callback to the StringVar
        self.frames[TimelinePage].gui['tFrame'].image_in_from_frame()

    def align_all_positions_to_refs(self):
        # image and align all images. First zoomed out, then zoomed it
        # set imaging options to reference type
        for pos_id in self.positions.keys():
            self.set_reference_imaging_conditions()
            self.image_new_position(pos_id=pos_id, ref_zoom=True)
            self.set_normal_imaging_conditions()
            self.image_new_position(pos_id=pos_id, ref_zoom=False)


class SharedFigs(dict):

    def __init__(self, fig_dpi, *args, **kwargs):
        super(SharedFigs, self).__init__()

        # Shared Timeline Figure
        self['timeline_figure'] = Figure(figsize=(5, 2), dpi=fig_dpi)
        self['timeline_figure'].set_tight_layout(True)
        self['timeline_axis'] = self['timeline_figure'].add_subplot(111)

        # Shared Positions Figure
        self['f_positions'] = Figure(figsize=(3, 3), dpi=fig_dpi)
        self['f_positions'].subplots_adjust(left=0, right=1, bottom=0, top=1)
        self['f_positions'].set_tight_layout(True)
        self['f_positions'].set_size_inches(4, 4)


###################


if __name__ == "__main__":
    app = SpineTracker(sys.argv[1:])
    try:
        app.mainloop()
    except(KeyboardInterrupt, SystemExit):
        raise
