import os
import pickle
from collections.abc import Mapping
from queue import Queue

from scipy import ndimage
from skimage import io, transform
from app.MainGuiBuilder import MainGuiBuilder
from app.inherited.inherited.inherited.SpineTrackerSettings import SettingsManager, CommandLineInterpreter
from io_communication.CommandReader import CommandReader
from io_communication.CommandWriter import CommandWriter
from io_communication.file_listeners import InstructionThread
from utilities.helper_functions import initialize_init_directory
import numpy as np
import copy
from utilities.math_helpers import measure_focus, compute_drift


class SpineTracker:

    def __init__(self, *args, **kwargs):
        self.args = args
        self.settings = self.initialize_settings()
        self.command_line_interpreter = self.initialize_command_line_interpreter()
        self.gui = self.initialize_guis()
        self.communication = self.initialize_communication()
        self.timeline = Timeline(self.settings)
        self.positions = Positions(self.settings)
        self.current_session = Session(self.settings, self.gui, self.positions)

        # TODO: This should go somewhere else...
        initialize_init_directory(self.settings.get('init_directory'))
        self.log_file = open('log.txt', 'w')

    def initialize_settings(self):
        settings = SettingsManager(self)
        settings.initialize_settings()
        return settings

    def initialize_guis(self):
        return MainGuiBuilder(self.settings)

    def initialize_command_line_interpreter(self):
        command_line_interpreter = CommandLineInterpreter(self.settings, self.args)
        command_line_interpreter.interpret()
        return command_line_interpreter

    def initialize_communication(self):
        return Communication(self.settings)


class Session:

    def __init__(self, settings, gui, positions):
        self.settings = settings
        self.gui = gui
        self.positions = positions
        self.timer_steps_queue = Queue()
        self.step_running = False
        self.current_pos_id = 1
        # TODO: Sequester these into a separate images dict or something
        self.current_image = AcquiredImage(settings)
        self.reference_image = ReferenceImage(settings)
        self.reference_image_zoomed_out = ReferenceImage(settings)
        self.macro_image = MacroImage(settings)

    def start_expt_log(self):
        file_path = self.settings.get('experiment_log_file')
        open(file_path, 'a').close()

    def write_to_expt_log(self, line):
        file_path = self.settings.get('experiment_log_file')
        with open(file_path, "a") as file:
            file.write(line + '\n')

    # TODO : Switch the update_figure thing to a higher function
    def load_image(self, update_figure=True, image_type='standard'):
        self.current_image.load()
        if image_type == 'standard':
            self.macro_image.load()
        elif image_type == 'reference':
            self.current_image.load()
        elif image_type == 'macro':
            self.macro_image.load()
        if update_figure:
            self.gui.reset_figure_for_af_images()

    def correct_xyz_drift(self, pos_id=None, ref_zoom=None):
        if pos_id is None:
            pos_id = self.current_pos_id
        # TODO: identify whether this is a zoomed out or regular reference image
        reference_max_projection = self.reference_image.get_max_projection()
        self.current_image.calc_x_y_z_drift(reference_max_projection)
        self.positions[pos_id]['x'] -= self.current_image.drift_x_y_z.x
        self.positions[pos_id]['y'] += self.current_image.drift_x_y_z.y
        self.positions[pos_id]['z'] += self.current_image.drift_x_y_z.z
        self.gui.post_drift(self.current_image.drift_x_y_z)
        # TODO: Left off here. send a signal to self.gui probably for this.
        self.show_new_images(pos_id=pos_id)
        self.backup_positions()


# TODO: reference and macro images can inherit this class and overwrite some options
class AcquiredImage:

    def __init__(self, settings):
        self.settings = settings
        self.image_stack = np.array([])
        self.is_macro = False
        self.is_reference = False
        self.zoom = 1
        self.pos_id = 1
        self.drift_x_y_z_history = []
        self.drift_x_y_z = DriftXYZ()

    def load(self):
        image_file_path = self.settings.get('image_file_path')
        total_chan = int(self.settings.get('total_channels'))
        drift_chan = int(self.settings.get('drift_correction_channel'))
        image_stack = io.imread(image_file_path)
        image_stack = image_stack[np.arange(drift_chan - 1, len(image_stack), total_chan)]
        self.image_stack = image_stack

    def calc_x_y_z_drift(self, reference_max_projection):
        # shape = self.settings.get('image_stack')[0].shape
        self.drift_x_y_z.compute_drift_z(self.image_stack)
        self.calc_x_y_drift(reference_max_projection)
        # TODO This is probably a mutable object so it'll change in the list? gotta figure out a way to copy it
        self.drift_x_y_z_history.append(self.drift_x_y_z.copy())


    def get_max_projection(self):
        return np.max(self.image_stack.copy(), axis=0)

    def calc_x_y_drift(self, reference_max_projection):
        image_max_projection = self.get_max_projection()
        reference_resized = transform.resize(reference_max_projection, image_max_projection.shape)
        fov_x_y = self.settings.get('fov_x_y')
        self.drift_x_y_z.compute_drift_x_y(reference_resized, image_max_projection)
        self.drift_x_y_z.scale_x_y_drift_to_image(fov_x_y, self.zoom, image_max_projection.shape)



class DriftXYZ:

    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.focus_list = np.array([])

    def copy(self):
        return copy.deepcopy(self)

    def compute_drift_z(self, image_stack):
        focus_list = []
        for image_slice in image_stack:
            focus_list.append(self.measure_focus(image_slice))
        focus_list = np.array(focus_list)
        drift_z = focus_list.argmax().item() - np.floor(len(image_stack) / 2)
        self.z = drift_z
        self.focus_list = focus_list

    def measure_focus(self, image):
        # Gaussian derivative (Geusebroek2000)
        w_size = 15
        nn = np.floor(w_size / 2)
        sig = nn / 2.5
        r = np.arange(-nn.astype(int), nn.astype(int) + 1)
        x, y = np.meshgrid(r, r)
        gg = np.exp(-(x ** 2 + y ** 2) / (2 * sig ** 2)) / (2 * np.pi * sig)
        gx = -x * gg / (sig ** 2)
        gx = gx / np.sum(gx, 1)
        gy = -y * gg / (sig ** 2)
        gy = gy / np.sum(gy)
        ry = ndimage.convolve(image.astype(float), gx, mode='nearest')
        rx = ndimage.convolve(image.astype(float), gy, mode='nearest')
        f_m = rx ** 2 + ry ** 2
        f_m = np.mean(f_m)
        return f_m

    def compute_drift_x_y(self, img_ref, img):
        h, w = img_ref.shape
        fft_ref = np.fft.fft2(img_ref)
        fft_img = np.fft.fft2(img)
        center_y = h / 2
        center_x = w / 2
        prod = fft_ref * np.conj(fft_img)
        cc = np.fft.ifft2(prod)
        max_y, max_x = np.nonzero(np.fft.fftshift(cc) == np.max(cc))
        shift_y = max_y - center_y
        shift_x = max_x - center_x
        # Checks to see if there is an ambiguity problem with FFT because of the
        # periodic boundary in FFT (not sure why or if this is necessary but I'm
        # keeping it around for now)
        if np.abs(shift_y) > h / 2:
            shift_y = shift_y - np.sign(shift_y) * h
        if np.abs(shift_x) > h / 2:
            shift_x = shift_x - np.sign(shift_x) * w
        self.x = shift_x
        self.y = shift_y

    def scale_x_y_drift_to_image(self, fov_x_y, zoom, image_shape):
        self.x, self.y = np.array([self.x, self.y]) / image_shape * fov_x_y / zoom


class ReferenceImage(AcquiredImage):

    def __init__(self, settings):
        super(ReferenceImage, self).__init__(settings)
        self.is_reference = True


class MacroImage(AcquiredImage):

    def __init__(self, settings):
        super(MacroImage, self).__init__(settings)
        self.is_macro = True


class Communication:

    def __init__(self, settings):
        self.settings = settings
        self.instructions_received = []
        self.instructions_in_queue = Queue()
        self.command_writer = CommandWriter(self.settings)
        self.command_reader = CommandReader(self.settings, self.instructions_in_queue, self.instructions_received)
        self.instructions_listener_thread = self.initialize_instructions_listener_thread()

    def initialize_instructions_listener_thread(self):
        input_file = self.settings.get('input_file')
        path, filename = os.path.split(input_file)
        read_function = self.command_reader.read_new_commands
        with self.instructions_in_queue.mutex:
            self.instructions_in_queue.queue.clear()
            instructions_listener_thread = InstructionThread(self, path, filename, read_function)
            instructions_listener_thread.start()
        return instructions_listener_thread


class Timeline:

    def __init__(self, settings):
        self.settings = settings
        self.timeline_steps = self.initialize_timeline_steps()

    def initialize_timeline_steps(self):
        file_name = self.settings.get('init_directory') + 'timeline_steps.p'
        if os.path.isfile(file_name):
            timeline_steps = pickle.load(open(file_name, 'rb'))
        else:
            timeline_steps = TimelineSteps(self.settings)
        return timeline_steps


class TimelineSteps(dict):

    def __init__(self, settings):
        super(TimelineSteps, self).__init__()
        self.settings = settings


class Positions(dict):

    def __init__(self, settings):
        super(Positions, self).__init__()
        self.settings = settings


############# Stuff to translate
#
# # -*- coding: utf-8 -*-
# """
# Created on Wed Oct 18 14:36:57 2017
#
# @author: smirnovm
# """
# import copy
# import datetime as dt
# import inspect
# import os
# import pickle
# from queue import Queue
#
# import matplotlib
# import numpy as np
# import sys
# from matplotlib import patches
# from matplotlib import style
# from matplotlib.figure import Figure
# from skimage import io, transform
#
# from app.inherited.InputOutputInterface import InputOutputInterface
# from flow.TimelineStep import TimelineStep
# from guis.MacroWindow import MacroWindow
# from guis.PositionsPage import PositionsPage
# from guis.SettingsPage import SettingsPage
# from guis.StartPage import StartPage
# from guis.TimelinePage import TimelinePage
# from io_communication.file_listeners import InstructionThread
# from utilities.helper_functions import initialize_init_directory
# from utilities.math_helpers import measure_focus, compute_drift
#
# matplotlib.use("TkAgg")
# style.use("ggplot")


class SpineTracker(InputOutputInterface):

    def __init__(self, *args, **kwargs):
        # super(SpineTracker, self).__init__(*args, **kwargs)

        self.timeline_steps_general = []  # should be initialized in another class (Timeline)

        # set properties for main window
        # self.protocol("WM_DELETE_WINDOW", self.on_exit)
        # define container for what's in the window

        # self.initialize_timeline_steps_general()
        # self.initialize_positions()
        # self.frames = {}
        # self.windows = {}
        # self.step_running = False
        # self.instructions_in_queue = Queue()
        # self.timer_steps_queue = Queue()

        # Shared Figures
        # self.shared_figs = SharedFigs(self.settings.get('fig_dpi'))

        # initialize instructions listener
        # path, filename = os.path.split(self.inputFile)
        # with self.instructions_in_queue.mutex:
        #     self.instructions_in_queue.queue.clear()
        # self.ins_thread = InstructionThread(self, path, filename, self.command_reader.read_new_commands)
        # self.ins_thread.start()

        # self.settings.set('center_xyz', np.array((0, 0, 0)))
        # initialize_init_directory(self.settings.get('init_directory'))
        # create/refresh log file
        # self.log_file = open('log.txt', 'w')

        # define frames (windows) available which will appear in main window
        # for F in (StartPage, SettingsPage, PositionsPage, TimelinePage):
        #     frame = F(self.container, self)
        #     self.frames[F] = frame
        #     self.container.add(frame, text=F.name)

        # self.current_pos_id = 1

    # def build_macro_window(self):
    #     self.windows[MacroWindow] = MacroWindow(self)

    # def on_exit(self):
    #     print('quitting')
    #     self.ins_thread.stop()
    #     print('Instruction listener closed')
    #     self.log_file.close()
    #     self.destroy()
    #     print('goodbye')

    # def start_expt_log(self):
    #     file_path = self.settings.get('experiment_log_file')
    #     open(file_path, 'a').close()

    # def write_to_log(self, line):
    #     file_path = self.settings.get('experiment_log_file')
    #     with open(file_path, "a") as f:
    #         f.write(line + '\n')

    # def initialize_timeline_steps_general(self):
    #     file_name = self.settings.get('init_directory') + 'timeline_steps.p'
    #     if os.path.isfile(file_name):
    #         self.timeline_steps_general = pickle.load(open(file_name, 'rb'))

    # TODO: put this in testing environment
    # def load_test_image(self, event):  # for test purposes only
    #     image = io.imread("../test/test_image.tif")
    #     image = image[np.arange(0, len(image), 2)]
    #     self.settings.set('image_stack', image)
    #     self.reset_figure_for_af_images()

    # def load_image(self, update_figure=True, get_macro=False):
    #     image = io.imread(self.image_file_path)
    #     total_chan = int(self.settings.get('total_channels'))
    #     drift_chan = int(self.settings.get('drift_correction_channel'))
    #     image = image[np.arange(drift_chan - 1, len(image), total_chan)]
    #     self.settings.set('image_stack', image)
    #     if get_macro:
    #         self.settings.set('macro_image', image)
    #     if update_figure:
    #         self.reset_figure_for_af_images()

    # TODO : put this in testing environment
    # def load_test_ref_image(self):  # for test purposes only
    #     imgref = io.imread("../test/test_refimg.tif")
    #     self.settings.set('imgref_imaging', imgref)
    #     self.settings.set('imgref_ref', imgref)

    def correct_xyz_drift(self, pos_id=None, ref_zoom=None):
        # if self.settings.get('image_stack') not in self.acq:
        #     return
        if pos_id is None:
            pos_id = self.current_pos_id
        shape = self.settings.get('image_stack')[0].shape
        self.settings.set('imgref_imaging', transform.resize(self.positions[pos_id]['ref_img'], shape))
        self.settings.set('imgref_ref', transform.resize(self.positions[pos_id]['ref_img_zoomout'], shape))
        self.calc_focus()
        self.calc_drift(ref_zoom)
        # x, y, z = [self.positions[pos_id][key] for key in ['x', 'y', 'z']]
        shiftx, shifty = self.settings.get('shiftxy')
        shiftz = self.settings.get('shiftz')
        self.positions[pos_id]['x'] -= shiftx
        self.positions[pos_id]['y'] += shifty
        self.positions[pos_id]['z'] += shiftz
        self.positions[pos_id]['xyzShift'] = self.positions[pos_id]['xyzShift'] + np.array([shiftx, shifty, shiftz])
        self.frames[StartPage].gui['drift_label'].configure(
            text='Detected drift of {0:.1f}µm in x and {1:.1f}µm in y'.format(shiftx.item(), shifty.item()))
        self.show_new_images(pos_id=pos_id)
        self.backup_positions()

    def show_new_images(self, pos_id=None):
        image = self.settings.get('image_stack')
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
        max_ind = self.settings.get('focus_list').argmax().item()
        siz = image[0].shape
        rect = patches.Rectangle((0, 0), siz[0], siz[1], fill=False, linewidth=5, edgecolor='r')
        a[max_ind].add_patch(rect)
        # add arrow to show shift in x,y
        center = np.array([siz[0] / 2, siz[1] / 2])
        shiftx, shifty = self.settings.get('shiftxy_pixels')['shiftx'], self.settings.get('shiftxy_pixels')['shifty']
        arrow = patches.Arrow(center[1] - shiftx, center[0] - shifty, shiftx, shifty, width=10, color='r')
        a[max_ind].add_patch(arrow)
        if pos_id is not None:
            self.frames[PositionsPage].select_position_in_graph(pos_id)
        self.frames[StartPage].gui['canvas_positions'].draw_idle()
        self.frames[StartPage].gui['canvas_af'].draw_idle()

    # def calc_focus(self):
    #     image_stack = self.settings.get('image_stack')
    #     focus_list = np.array([])
    #     for image in image_stack:
    #         focus_list = np.append(focus_list, (measure_focus(image)))
    #     self.settings.set('shiftz', focus_list.argmax().item() - np.floor(len(image_stack) / 2))
    #     self.settings.set('focus_list', focus_list)

    def calc_drift(self, ref_zoom=None):
        image = np.max(self.settings.get('image_stack'), 0)
        zoom = np.float(self.settings.get('current_zoom'))
        fov_x_y = self.settings['fov_x_y']
        if ref_zoom is None:
            ref_zoom = (self.settings.get('current_zoom') == float(self.settings.get('reference_zoom')))
        if ref_zoom:
            imgref = self.settings.get('imgref_ref')
        else:
            imgref = self.settings.get('imgref_imaging')
        self.settings.set('shiftxy_pixels', compute_drift(imgref, image))
        shiftx, shifty = np.array(
            [self.settings.get('shiftxy_pixels')['shiftx'],
             self.settings.get('shiftxy_pixels')['shifty']]) / image.shape * fov_x_y / zoom
        self.settings.set('shiftxy', (shiftx, shifty))

    def reset_figure_for_af_images(self):
        # if 'image_stack' not in self.acq:
        #     return
        image = self.settings.get('image_stack')
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
            self.timeline_steps_general.append(timeline_step)
        else:
            self.timeline_steps_general.insert(index, timeline_step)

        self.frames[TimelinePage].draw_timeline_steps_general()

    def add_step_to_queue(self, step, pos_id):
        single_step = copy.copy(step)  # .copy() returns dict, not TimelineStep object
        single_step['pos_id'] = pos_id
        self.timer_steps_queue.put(single_step)

    def run_step_from_queue(self):
        while self.imagingActive:
            # update() function on the GUI is necessary to keep it active
            self.update()
            if self.step_running:  # make sure something isn't already running
                continue
            if not self.timer_steps_queue.empty():
                single_step = self.timer_steps_queue.get()
            else:
                continue
            self.step_running = True
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
        self.write_to_log('Position {}: {}'.format(pos_id, self.image_file_path))
        if single_step is not None:
            self.step_running = False
        self.load_image()
        self.correct_xyz_drift(pos_id, ref_zoom=ref_zoom)

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
            self.step_running = False

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
