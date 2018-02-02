# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 14:36:57 2017

@author: smirnovm
"""

import tkinter as tk
from tkinter import ttk
import matplotlib
import numpy as np
import datetime as dt
import pickle
import os
import inspect
from matplotlib.figure import Figure
from skimage import io, transform
from matplotlib import style
from matplotlib import patches
from queue import Queue

from guis.MacroWindow import MacroWindow
from guis.PositionsPage import PositionsPage
from guis.SettingsPage import SettingsPage
from guis.StartPage import StartPage
from guis.TimelinePage import TimelinePage
from io_communication.GetCommands import GetCommands
from io_communication.SendCommands import SendCommands
from io_communication.file_listeners import InstructionThread
from utilities.helper_functions import initialize_init_directory
from utilities.math_helpers import focus_measure, compute_drift

matplotlib.use("TkAgg")
style.use("ggplot")


class SpineTracker(tk.Tk):

    def __init__(self, *args, **kwargs):

        tk.Tk.__init__(self, *args, **kwargs)  # initialize regular Tk stuff

        # set properties for main window
        self.settings = {}
        self.timelineSteps = []
        self.positions = {}
        self.app_params = dict(large_font=("Verdana", 12),
                               fig_dpi=100,
                               simlulation=True,
                               verbose=True,
                               initDirectory="../iniFiles/")
        tk.Tk.iconbitmap(self, default="../images/crabIco.ico")  # icon doesn't work
        tk.Tk.wm_title(self, "SpineTracker")
        tk.Tk.geometry(self, newGeometry='1000x600+200+200')
        self.protocol("WM_DELETE_WINDOW", self.on_exit)
        # define container for what's in the window
        container = ttk.Notebook(self)
        container.pack(side="top", fill="both", expand=True)
        self.initialize_timeline_steps()
        self.initialize_positions()
        self.load_settings()
        self.frames = {}
        self.windows = {}
        self.acq = {}
        self.measure = {}
        self.stepRunning = False
        self.instructions = []
        self.instructions_in_queue = Queue()
        self.timerStepsQueue = Queue()
        self.outputFile = "../instructions_output.txt"
        self.inputFile = "../instructions_input.txt"
        self.sendCommands = SendCommands(self, self.outputFile)
        self.getCommands = GetCommands(self, self.inputFile)

        # Shared Timeline Figure
        self.shared_figs = dict()
        self.shared_figs['f_timeline'] = Figure(figsize=(5, 2), dpi=self.get_app_param('fig_dpi'))
        self.shared_figs['f_timeline'].set_tight_layout(True)
        self.shared_figs['a_timeline'] = self.shared_figs['f_timeline'].add_subplot(111)

        # Shared Positions Figure
        self.shared_figs['f_positions'] = Figure(figsize=(3, 3), dpi=self.get_app_param('fig_dpi'))
        self.shared_figs['f_positions'].subplots_adjust(left=0, right=1, bottom=0, top=1)
        self.shared_figs['f_positions'].set_tight_layout(True)
        self.shared_figs['f_positions'].set_size_inches(4, 4)


        # initialize instructions listener
        path, filename = os.path.split(self.inputFile)
        with self.instructions_in_queue.mutex:
            self.instructions_in_queue.queue.clear()
        self.ins_thread = InstructionThread(self, path, filename, self.getCommands.read_new_instructions)
        self.ins_thread.start()

        self.centerXY = (0, 0)
        initialize_init_directory(self.get_app_param('initDirectory'))
        # create/refresh log file
        self.log_file = open('log.txt', 'w')

        # define frames (windows) available which will appear in main window
        for F in (StartPage, SettingsPage, PositionsPage, TimelinePage):
            frame = F(container, self)
            self.frames[F] = frame
            container.add(frame, text=F.name)

        self.currentPosID = 1

    def set_app_param(self, k, v):
        self.app_params[k] = v

    def get_app_param(self, k, *args):
        param = self.app_params.get(k, None)
        if param is None and args:
            param = args[0]
        return param

    def get_settings(self,k, *args):
        setting = self.settings.get(k, None)
        if setting is None and args:
            setting = args[0]
        return setting

    def show_macro_view_window(self):
        self.windows[MacroWindow] = MacroWindow(self)

    def on_exit(self):
        print('quitting')
        try:
            self.ins_thread.stop()
            print('Instruction listener closed')
        except:  # TODO: Make more specific except clause
            pass
        self.log_file.close()
        self.destroy()
        print('goodbye')

    # def listen_to_instructions_file(self):
    #     path, filename = os.path.split(self.inputFile)
    #     with self.instructions_in_queue.mutex:
    #         self.instructions_in_queue.queue.clear()
    #     self.ins_thread = InstructionThread(self, path, filename, self.getCommands.readNewInstructions)

    def initialize_positions(self):
        try:
            self.positions = pickle.load(open(self.get_app_param('initDirectory') + 'positions.p', 'rb'))
        except:
            pass

    def initialize_timeline_steps(self):
        try:
            self.timelineSteps = pickle.load(open(self.get_app_param('initDirectory') + 'timelineSteps.p', 'rb'))
        except:
            pass

    def load_settings(self):
        try:
            self.settings = pickle.load(open(self.get_app_param('initDirectory') + 'user_settings.p', 'rb'))
        except:
            pass
        self.check_settings()

    def check_settings(self):
        default_settings = {'driftCorrectionChannel': 1,
                            'fovXY': (250, 250),
                            'stagger': 10,
                            'totalChannels': 2,
                            'imagingZoom': 30,
                            'imagingSlices': 3,
                            'referenceZoom': 15,
                            'referenceSlices': 10
                            }
        flag = False
        for key in default_settings:
            if key not in self.settings.keys():
                self.settings[key] = default_settings[key]
                flag = True
        if flag:
            self.save_settings()

        # measure autofocus of image

    def load_test_image(self):  # for testing purposes only
        image = io.imread("../testing/test_image.tif")
        image = image[np.arange(0, len(image), 2)]
        self.acq['imageStack'] = image
        self.create_figure_for_af_images()

    #        return(image)

    def load_acquired_image(self, update_figure=True):
        image = io.imread(self.imageFilePath)
        total_chan = int(self.frames[SettingsPage].totalChannelsVar.get())
        drift_chan = int(self.frames[SettingsPage].driftCorrectionChannelVar.get())
        image = image[np.arange(drift_chan - 1, len(image), total_chan)]
        self.acq['imageStack'] = image
        if update_figure:
            self.create_figure_for_af_images()

    def load_test_ref_image(self):  # for testing purposes only
        imgref = io.imread("../testing/test_refimg.tif")
        #        self.acq['imgref'] = imgref
        self.acq['imgref_imaging'] = imgref
        self.acq['imgref_ref'] = imgref

    #        return(imgref)

    def run_xyz_drift_correction(self, pos_id=None):
        if 'imageStack' not in self.acq:
            return
        if pos_id is None:
            pos_id = self.currentPosID
        shape = self.acq['imageStack'][0].shape
        self.acq['imgref_imaging'] = transform.resize(self.positions[pos_id]['refImg'], shape)
        self.acq['imgref_ref'] = transform.resize(self.positions[pos_id]['refImgZoomout'], shape)
        self.calc_focus()
        self.calc_drift()
        x, y, z = [self.positions[pos_id][key] for key in ['x', 'y', 'z']]
        shiftx, shifty = self.measure['shiftxy']
        shiftz = self.measure['shiftz']
        self.positions[pos_id]['x'] = x + shiftx
        self.positions[pos_id]['y'] = y + shifty
        self.positions[pos_id]['z'] = z + shiftz
        self.positions[pos_id]['xyzShift'] = self.positions[pos_id]['xyzShift'] + np.array([shiftx, shifty, shiftz])
        self.frames[StartPage].driftLabel.configure(
            text='Detected drift of {0}px in x and {1}px in y'.format(shiftx.item(), shifty.item()))
        self.show_new_images()

    def show_new_images(self):
        image = self.acq['imageStack']
        i = 0
        a = self.AFImageAx
        # show images
        for im in image:
            a[i].clear()
            a[i].imshow(im)
            a[i].axis('equal')
            a[i].axis('off')
            i += 1
        # show best focused image
        max_ind = self.measure['FMlist'].argmax().item()
        siz = image[0].shape
        rect = patches.Rectangle((0, 0), siz[0], siz[1], fill=False, linewidth=5, edgecolor='r')
        a[max_ind].add_patch(rect)
        self.frames[StartPage].canvas['canvas_af'].draw_idle()

    def calc_focus(self):
        image = self.acq['imageStack']
        fm = np.array([])
        for im in image:
            fm = np.append(fm, (focus_measure(im)))
        self.measure['shiftz'] = fm.argmax().item() - np.floor(
            len(image) / 2)  # this needs to be checked obviously, depending on how Z info is dealt with
        self.measure['FMlist'] = fm

    def calc_drift(self):
        image = np.max(self.acq['imageStack'], 0)
        if self.acq['currentZoom'] == float(self.frames[PositionsPage].imagingZoom.get()):
            imgref = self.acq['imgref_imaging']
        else:
            imgref = self.acq['imgref_ref']
        shift = compute_drift(imgref, image)
        shiftx = shift['shiftx']
        shifty = shift['shifty']
        self.measure['shiftxy'] = (shiftx, shifty)

    def create_figure_for_af_images(self):
        if 'imageStack' not in self.acq:
            return
        image = self.acq['imageStack']
        subplot_length = len(image)
        f = self.frames[StartPage].fig_af_image
        a = self.frames[StartPage].ax_af_image
        for ax in a.copy():
            try:
                a.remove(ax)
                f.delaxes(ax)
            except:
                self.print_status('axes delete not working')
        for i in range(subplot_length):
            a.append(f.add_subplot(1, subplot_length, i + 1))

    def get_current_position(self):
        if self.get_app_param('simulation'):
            # simulate position for now.
            # eventually, pull position from other program here
            x = np.random.randint(-100, 100)
            y = np.random.randint(-100, 100)
            z = np.random.randint(-100, 100)
        else:
            flag = 'currentPosition'
            self.getCommands.receivedFlags[flag] = False
            self.sendCommands.get_current_position()
            self.getCommands.wait_for_received_flag(flag)
            x, y, z = self.currentCoordinates
        return {'x': x, 'y': y, 'z': z}

    def create_new_pos(self, xyz, ref_images=None):
        # just starting with an empty dict for now
        if len(self.positions) == 0:
            pos_id = 1
        else:
            pos_id = max(self.positions.keys()) + 1
        self.positions[pos_id] = xyz
        if ref_images is None:
            # load sample ref images
            self.load_test_ref_image()
        else:
            self.acq['imgref_imaging'] = ref_images['imaging']
            self.acq['imgref_ref'] = ref_images['ref']
        self.positions[pos_id]['refImg'] = self.acq['imgref_imaging']
        self.positions[pos_id]['refImgZoomout'] = self.acq['imgref_ref']
        self.positions[pos_id]['xyzShift'] = np.array([0, 0, 0])
        roipos = np.array(self.positions[pos_id]['refImg'].shape) / 2
        self.positions[pos_id]['roi_position'] = roipos

    def add_position(self, cont, xyz=None, ref_images=None):
        if xyz is None:
            xyz = self.get_current_position()
        # add position to table
        self.create_new_pos(xyz, ref_images=ref_images)
        cont.redraw_position_table()
        self.backup_positions()

    def clear_positions(self, cont):
        self.positions = {}
        cont.redraw_position_table()

    def delete_positions(self, pos_id):
        del self.positions[pos_id]
        self.frames[PositionsPage].redraw_position_table()
        self.backup_positions()

    def update_position(self, pos_id):
        xyz = self.get_current_position()
        self.positions[pos_id].update(xyz)
        self.frames[PositionsPage].redraw_position_table()
        self.backup_positions()

    def add_timeline_step(self, step_dict, ind=None):
        print("step name: {0}, type: {1}, Period: {2}s, Duration: {3}min".format(
            step_dict['SN'], step_dict['IU'], step_dict['P'], step_dict['D']))
        if ind is None:
            self.timelineSteps.append(step_dict)
        else:
            self.timelineSteps.insert(ind, step_dict)

        self.frames[TimelinePage].draw_timeline_steps()

    def backup_positions(self):
        positions = self.positions
        pickle.dump(positions, open(self.get_app_param('initDirectory') + 'positions.p', 'wb'))

    def update_settings(self, key, source):
        self.settings[key] = source.get()
        self.save_settings()

    def save_settings(self):
        user_settings = self.settings
        pickle.dump(user_settings, open(self.get_app_param('initDirectory') + 'user_settings.p', 'wb'))

    def add_step_to_queue(self, step, pos_id):
        step = step.copy()
        step.update(dict(posID=pos_id))
        self.timerStepsQueue.put(step)

    def run_step_from_queue(self):
        while self.imagingActive:
            # update() function on the GUI is necessary to keep it active
            self.update()
            if self.stepRunning:  # make sure something isn't already running
                continue
            if not self.timerStepsQueue.empty():
                step = self.timerStepsQueue.get()
            else:
                continue
            self.stepRunning = True
            pos_id = step['pos_id']
            if step['EX']:
                ex = 'Exclusive'
            else:
                ex = 'Non-Exclusive'
            print('{0} {1} Timer {2} running at {3}s '.format(ex, step['IU'], pos_id, dt.datetime.now().second))

            # this should actually be set once data from position is received, because drift/af calculation will be
            # done after that
            self.currentPosID = pos_id
            # we're already in a thread so maybe don't need another one here
            if step['IU'] == 'Image':
                self.image_new_position(step)
            elif step['IU'] == 'Uncage':
                self.uncage_new_position(step)

    def image_new_position(self, step):
        pos_id, x, y, z = self.parse_step(step)
        self.move_stage(x, y, z)
        self.grab_stack()
        self.stepRunning = False
        self.load_acquired_image()
        self.run_xyz_drift_correction(pos_id)

    def uncage_new_position(self, step):
        pos_id, x, y, z = self.parse_step(step)
        roi_x, roi_y = self.positions[pos_id]['roi_position']
        self.move_stage(x, y, z)
        self.uncage(roi_x, roi_y)
        self.stepRunning = False

    def parse_step(self, step):
        pos_id = step['pos_id']
        x, y, z = [self.positions[pos_id][xyz] for xyz in ['x', 'y', 'z']]
        return pos_id, x, y, z

    def move_stage(self, x, y, z):
        if self.parkXYmotor:
            x_motor, y_motor = self.centerXY
            self.set_scan_shift(x, y)
        else:
            x_motor = x
            y_motor = y
        flag = 'stageMoveDone'
        self.getCommands.receivedFlags[flag] = False
        self.sendCommands.move_stage(x_motor, y_motor, z)
        self.getCommands.wait_for_received_flag(flag)

    def grab_stack(self):
        flag = 'grabOneStackDone'
        self.getCommands.receivedFlags[flag] = False
        self.sendCommands.grab_one_stack()
        self.getCommands.wait_for_received_flag(flag)

    def uncage(self, roi_x, roi_y):
        flag = 'uncagingDone'
        self.getCommands.receivedFlags[flag] = False
        self.sendCommands.do_uncaging(roi_x, roi_y)
        self.getCommands.wait_for_received_flag(flag)

    def set_scan_shift(self, x, y):
        scan_shift_fast, scan_shift_slow = self.xy_to_scan_angle(x, y)
        flag = 'scanAngleXY'
        self.getCommands.receivedFlags[flag] = False
        self.sendCommands.set_scan_shift(scan_shift_fast, scan_shift_slow)
        self.getCommands.wait_for_received_flag(flag)

    def set_z_slice_num(self, z_slice_num):
        flag = 'z_slice_num'
        self.getCommands.receivedFlags[flag] = False
        self.sendCommands.set_z_slice_num(z_slice_num)
        self.getCommands.wait_for_received_flag(flag)

    def xy_to_scan_angle(self, x, y):
        scan_angle_multiplier = np.array(self.scanAngleMultiplier)
        scan_angle_range_reference = np.array(self.scanAngleRangeReference)
        fov = np.array(self.settings['fovXY'])
        # convert x and y to relative pixel coordinates
        x_center, y_center = self.centerXY
        xc = x - x_center
        yc = y - y_center
        fs_coordinates = np.array([xc, yc])
        scan_shift = np.array([0, 0])
        fs_normalized = fs_coordinates / fov
        fs_angular = scan_shift + fs_normalized * scan_angle_multiplier * scan_angle_range_reference
        scan_shift_fast, scan_shift_slow = fs_angular
        return scan_shift_fast, scan_shift_slow

    def get_scan_props(self):
        flag = 'scanAngleMultiplier'
        self.getCommands.receivedFlags[flag] = False
        self.sendCommands.get_scan_angle_multiplier()
        self.getCommands.wait_for_received_flag(flag)

        flag = 'scanAngleRangeReference'
        self.getCommands.receivedFlags[flag] = False
        self.sendCommands.get_scan_angle_range_reference()
        self.getCommands.wait_for_received_flag(flag)

    def set_zoom(self, zoom):
        flag = 'zoom'
        self.getCommands.receivedFlags[flag] = False
        self.sendCommands.set_zoom(zoom)
        self.getCommands.wait_for_received_flag(flag)

    def print_status(self, following_string):
        if self.app_params['verbose']:
            # following_string is a string to add after the function. something like Started or Finished
            string = '\nFunction {0} {1}\n'.format(inspect.stack()[1][3], following_string)
            print(string)
            self.log_file.write(string)


###################


if __name__ == "__main__":
    app = SpineTracker()
    try:
        app.mainloop()
    except(KeyboardInterrupt, SystemExit):
        raise
