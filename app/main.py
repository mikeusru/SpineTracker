import os
import pickle
import threading
from queue import Queue

from scipy import ndimage
from skimage import io, transform

from app.Coordinates import Coordinates
from app.PositionsManager import PositionsManager
from app.Timeline import Timeline
from app.guis import MainGuiBuilder
from app.settings import SettingsManager, CommandLineInterpreter
from flow.PositionTimer import PositionTimer
from guis import TimelinePage
from io_communication.CommandReader import CommandReader
from io_communication.CommandWriter import CommandWriter
from io_communication.file_listeners import InstructionThread
from utilities.helper_functions import initialize_init_directory
import numpy as np
import copy
import datetime as dt
import sys
from PIL import Image

from utilities.math_helpers import contrast_stretch


# TODO: Split up instantiation and loading stuff in
class SpineTracker:

    def __init__(self, *args, **kwargs):
        self.args = args
        self.settings = self.initialize_settings()
        self.command_line_interpreter = self.initialize_command_line_interpreter()
        self.communication = self.initialize_communication()
        self.positions = self.initialize_positions()
        self.timeline = Timeline(self.settings, self.positions)
        self.session = Session(self.settings,
                               self.positions,
                               self.communication,
                               self.timeline)
        self.gui = self.initialize_guis()
        # TODO: This should go somewhere else...
        initialize_init_directory(self.settings.get('init_directory'))
        self.log_file = open('log.txt', 'w')
        self.gui.bind_session(self.session)
        self.positions.bind_session(self.session)
        self.communication.bind_session(self.session)

    def initialize_settings(self):
        settings = SettingsManager(self)
        settings.initialize_settings()
        return settings

    def initialize_guis(self):
        return MainGuiBuilder(self.session)

    def initialize_command_line_interpreter(self):
        command_line_interpreter = CommandLineInterpreter(self.settings, self.args)
        command_line_interpreter.interpret()
        return command_line_interpreter

    def initialize_communication(self):
        return Communication(self.settings)

    def initialize_positions(self):
        positions = PositionsManager(self.settings)
        positions.load_previous_positions()
        return positions

    def mainloop(self):
        self.gui.mainloop()


class State:
    def __init__(self, session):
        self.session = session
        self.settings = session.settings
        self.step_running = False
        self.imaging_active = False
        self.current_pos_id = 1
        self.current_coordinates = Coordinates(self.settings)
        self.center_coordinates = Coordinates(self.settings)
        self.current_image = AcquiredImage(self.settings)
        self.ref_image = ReferenceImage(self.settings)
        self.ref_image_zoomed_out = ReferenceImage(self.settings)
        self.macro_image = MacroImage(self.settings)
        self.position_timers = {}
        self.queue_run = None


class Session:

    def __init__(self, settings, positions, communication, timeline):
        self.settings = settings
        self.gui = None
        self.positions = positions
        self.timeline = timeline
        self.communication = communication
        self.timer_steps_queue = TimerStepsQueue()
        self.state = State(self)

    def bind_guis(self, gui):
        self.gui = gui

    def start_expt_log(self):
        file_path = self.settings.get('experiment_log_file')
        open(file_path, 'a').close()

    def write_to_expt_log(self, line):
        file_path = self.settings.get('experiment_log_file')
        with open(file_path, "a") as file:
            file.write(line + '\n')

    def load_image(self, image_type='standard'):
        if image_type == 'standard':
            self.state.current_image.zoom = self.settings.get('imaging_zoom')
            self.state.current_image.load()
        elif image_type == 'zoomed_out':
            self.state.current_image.zoom = self.settings.get('reference_zoom')
            self.state.current_image.load()
        elif image_type == 'reference':
            self.state.ref_image.load()
        elif image_type == 'reference_zoomed_out':
            self.state.ref_image_zoomed_out.load()
        elif image_type == 'macro':
            self.state.macro_image.load()
            self.state.macro_image.set_image_contrast()
            self.state.macro_image.create_pil_image()
        else:
            print("WRONG IMAGE TYPE")
        # TODO: Throw error if it's some other kind of image
        if not image_type == 'macro':
            self.gui.reset_figure_for_af_images()

    def correct_xyz_drift(self, pos_id=None, zoom=None):
        if zoom is None:
            zoom = self.settings.get('imaging_zoom')
        if pos_id is None:
            pos_id = self.state.current_pos_id
        reference_max_projection = self.get_ref_image(zoom, pos_id)
        self.state.current_image.calc_x_y_z_drift(reference_max_projection)
        self.positions[pos_id]['x'] -= self.state.current_image.drift_x_y_z.x_um
        self.positions[pos_id]['y'] += self.state.current_image.drift_x_y_z.y_um
        self.positions[pos_id]['z'] += self.state.current_image.drift_x_y_z.z_um
        self.gui.show_drift_info(image_stack=self.state.current_image, pos_id=pos_id)
        self.positions.record_drift_history(self.state.current_image)
        self.positions.backup_positions()

    def get_ref_image(self, zoom, pos_id):
        if zoom == self.settings.get('reference_zoom'):
            reference_max_projection = self.positions.get_image(pos_id, zoomed_out=True).get_max_projection()
        else:
            reference_max_projection = self.positions.get_image(pos_id, zoomed_out=False).get_max_projection()
        return reference_max_projection

    def add_step_to_queue(self, step, pos_id):
        self.timer_steps_queue.add_step(step, pos_id)

    def run_steps_from_queue_when_appropriate(self):
        while self.state.current_image:
            self.prevent_freezing_during_loops()
            if self.state.step_running:
                continue
            if self.timer_steps_queue.empty():
                continue
            self.state.step_running = True
            self.timer_steps_queue.load_next_step()
            self.run_current_step()

    def run_current_step(self):
        single_step = self.timer_steps_queue.current_step
        pos_id = single_step.get('pos_id')
        self.state.current_pos_id = pos_id
        if single_step['imaging_or_uncaging'] == 'Image':
            self.image_at_pos_id(pos_id)
            self.state.step_running = False
            self.load_image()
            self.correct_xyz_drift(pos_id)
        elif single_step['imaging_or_uncaging'] == 'Uncage':
            self.uncage_at_pos_id(pos_id)
            self.state.step_running = False

    def prevent_freezing_during_loops(self):
        self.gui.update()

    def image_at_pos_id(self, pos_id):
        self.move_to_pos_id(pos_id)
        self.communication.grab_stack()
        self.record_imaging_to_log(pos_id)

    def uncage_at_pos_id(self, pos_id):
        self.move_to_pos_id(pos_id=pos_id)
        roi_x, roi_y = self.positions.get_roi_x_y(pos_id)
        self.record_uncaging_to_log(pos_id)
        self.communication.uncage(roi_x, roi_y)

    def align_all_positions_to_refs(self):
        for pos_id in self.positions.keys():
            self.communication.set_reference_imaging_conditions()
            self.image_at_pos_id(pos_id)
            self.load_image(image_type='zoomed_out')
            self.correct_xyz_drift(pos_id, zoom=self.settings.get('reference_zoom'))
            self.communication.set_normal_imaging_conditions()
            self.image_at_pos_id(pos_id)
            self.load_image(image_type='standard')
            self.correct_xyz_drift(pos_id, zoom=self.settings.get('imaging_zoom'))

    def record_imaging_to_log(self, pos_id):
        self.write_to_log('Position {}: {}'.format(pos_id, self.settings.get('image_file_path')))

    def record_uncaging_to_log(self, pos_id):
        self.write_to_log('Position {0}: Uncaging at {1}:{2}:{3}'.format(pos_id, dt.datetime.now().hour,
                                                                         dt.datetime.now().minute,
                                                                         dt.datetime.now().second))

    def create_new_position(self, take_new_refs=True):
        if take_new_refs:
            self.collect_new_reference_images()
            self.communication.get_current_position()
        self.positions.create_new_pos(self.state.ref_image, self.state.ref_image_zoomed_out)
        self.gui.update_positions_table()
        self.positions.backup_positions()

    def clear_positions(self):
        self.positions.clear()
        self.gui.update_positions_table()

    def remove_position(self, pos_id):
        self.positions.remove(pos_id)
        self.gui.update_positions_table()
        self.positions.backup_positions()

    def update_position(self, pos_id):
        xyz = self.communication.get_current_position()
        self.positions[pos_id].set_coordinates(xyz)
        self.gui.update_positions_table()
        self.positions.backup_positions()

    def collect_new_reference_images(self):
        self.communication.set_reference_imaging_conditions()
        self.communication.grab_stack()
        self.load_image('reference_zoomed_out')
        self.communication.set_normal_imaging_conditions()
        self.communication.grab_stack()
        self.load_image('reference')

    def collect_new_macro_image(self):
        self.communication.set_macro_imaging_conditions()
        self.communication.grab_stack()
        self.load_image('macro')

    def move_to_pos_id(self, pos_id):
        x, y, z = [self.positions[pos_id][key] for key in ['x', 'y', 'z']]
        self.communication.move_stage(x, y, z)

    def write_to_log(self, line):
        file_path = self.settings.get('experiment_log_file')
        with open(file_path, "a") as f:
            f.write(line + '\n')

    def update_timeline_chart(self, *args):
        self.gui.frames[TimelinePage].create_timeline_chart()

    def switch_between_image_and_uncage_guis(self, *args):
        self.gui.frames[TimelinePage].gui['tFrame'].image_in_from_frame()

    def start_imaging(self):
        self.communication.get_scan_props()
        self.communication.set_normal_imaging_conditions()
        self.state.position_timers = {}
        self.start_expt_log()
        self.timer_steps_queue.clear_timers()
        individual_steps = self.timeline.get_steps_for_queue()
        for pos_id in individual_steps:
            self.state.position_timers[pos_id] = PositionTimer(self, individual_steps[pos_id],
                                                         self.add_step_to_queue, pos_id)
        self.state.imaging_active = True
        self.state.queue_run = threading.Thread(target=self.run_steps_from_queue_when_appropriate)
        self.state.queue_run.daemon = True
        self.state.queue_run.start()

    def stop_imaging(self):
        for pos_id in self.state.position_timers:
            self.state.position_timers[pos_id].stop()
        self.state.imaging_active = False


class TimerStepsQueue(Queue):

    def __init__(self):
        super(TimerStepsQueue, self).__init__()
        self.current_step = None

    def add_step(self, step, pos_id):
        single_step = copy.copy(step)  # .copy() returns dict, not TimelineStepBlock object
        single_step['pos_id'] = pos_id
        self.put(single_step)

    def load_next_step(self):
        self.current_step = self.get()

        self.print_current_step_info()

    def print_current_step_info(self):
        single_step = self.current_step
        pos_id = self.current_step.get('pos_id')
        if single_step.get('exclusive'):
            ex = 'Exclusive'
        else:
            ex = 'Non-Exclusive'
        print('{0} {1} Timer {2} running at {3}:{4}:{5} '.format(ex, single_step['imaging_or_uncaging'], pos_id,
                                                                 dt.datetime.now().hour, dt.datetime.now().minute,
                                                                 dt.datetime.now().second))

    def clear_timers(self):
        with self.mutex:
            self.queue.clear()


class AcquiredImage:

    def __init__(self, settings):
        self.settings = settings
        self.image_stack = np.array([])
        self.is_macro = False
        self.is_reference = False
        self.zoom = settings.get('current_zoom')
        self.pos_id = 1
        self.drift_x_y_z = DriftXYZ()

    def load(self):
        image_file_path = self.settings.get('image_file_path')
        total_chan = int(self.settings.get('total_channels'))
        drift_chan = int(self.settings.get('drift_correction_channel'))
        image_stack = io.imread(image_file_path)
        image_stack = image_stack[np.arange(drift_chan - 1, len(image_stack), total_chan)]
        self.image_stack = image_stack

    def calc_x_y_z_drift(self, reference_max_projection):
        self.drift_x_y_z.compute_drift_z(self.image_stack)
        self.calc_x_y_drift(reference_max_projection)

    def get_max_projection(self):
        return np.max(self.image_stack.copy(), axis=0)

    def calc_x_y_drift(self, reference_max_projection):
        image_max_projection = self.get_max_projection()
        reference_resized = transform.resize(reference_max_projection, image_max_projection.shape)
        fov_x_y = self.settings.get('fov_x_y')
        self.drift_x_y_z.compute_drift_x_y(reference_resized, image_max_projection)
        self.drift_x_y_z.scale_x_y_drift_to_image(fov_x_y, self.zoom, image_max_projection.shape)

    def get_shape(self):
        return self.image_stack.shape


class ReferenceImage(AcquiredImage):

    def __init__(self, settings):
        super(ReferenceImage, self).__init__(settings)
        self.is_reference = True


class ReferenceImageZoomedOut(AcquiredImage):

    def __init__(self, settings):
        super(ReferenceImageZoomedOut, self).__init__(settings)
        self.is_reference = True
        self.zoom = settings.get('reference_zoom')


class MacroImage(AcquiredImage):

    def __init__(self, settings):
        super(MacroImage, self).__init__(settings)
        self.is_macro = True
        self.zoom = settings.get('macro_zoom')
        self.pil_image = None

    def set_image_contrast(self):
        self.image_stack = np.array([contrast_stretch(img) for img in self.image_stack])
        self.image_stack = self.image_stack / np.max(self.image_stack) * 255

    def create_pil_image(self):
        # since PIL doesn't support creating multiframe images, save the image and load it as a workaround for now.
        image_list = [Image.fromarray(image.astype(np.uint8)) for image in self.image_stack]
        image_list[0].save("../temp/macro_image.tif", compression="tiff_deflate", save_all=True,
                           append_images=image_list[1:])
        self.pil_image = Image.open("../temp/macro_image.tif")


# TODO: Add way to convert z_slices to z_um
class DriftXYZ:

    def __init__(self):
        self.x_pixels = 0
        self.x_um = 0
        self.y_pixels = 0
        self.y_um = 0
        self.z_slices = 0
        self.z_um = 0
        self.focus_list = np.array([])

    def copy(self):
        return copy.deepcopy(self)

    def compute_drift_z(self, image_stack):
        focus_list = []
        for image_slice in image_stack:
            focus_list.append(self.measure_focus(image_slice))
        focus_list = np.array(focus_list)
        drift_z = focus_list.argmax().item() - np.floor(len(image_stack) / 2)
        self.z_slices = drift_z
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
        self.x_pixels = shift_x
        self.y_pixels = shift_y

    def scale_x_y_drift_to_image(self, fov_x_y, zoom, image_shape):
        self.x_um, self.y_um = np.array([self.x_pixels, self.y_pixels]) / image_shape * fov_x_y / zoom


class Communication:

    def __init__(self, settings):
        self.settings = settings
        self.session = None
        self.instructions_received = []
        self.instructions_in_queue = Queue()
        self.command_writer = CommandWriter(self.settings)
        self.command_reader = CommandReader(self.settings, self.instructions_in_queue, self.instructions_received)
        self.instructions_listener_thread = self.initialize_instructions_listener_thread()

    def bind_session(self, session):
        self.session = session
        self.command_reader.bind_session(session)

    def initialize_instructions_listener_thread(self):
        input_file = self.settings.get('input_file')
        path, filename = os.path.split(input_file)
        read_function = self.command_reader.read_new_commands
        with self.instructions_in_queue.mutex:
            self.instructions_in_queue.queue.clear()
            instructions_listener_thread = InstructionThread(self, path, filename, read_function)
            instructions_listener_thread.start()
        return instructions_listener_thread

    def move_stage(self, x=None, y=None, z=None):
        if self.settings.get('park_xy_motor'):
            x_motor, y_motor, _ = self.session.state.center_coordinates.get_motor_coordinates()
            self.set_scan_shift(x, y)
        else:
            x_motor = x
            y_motor = y
        flag = 'stage_move_done'
        self.command_reader.received_flags[flag] = False
        self.command_writer.move_stage(x_motor, y_motor, z)
        self.command_reader.wait_for_received_flag(flag)

    def grab_stack(self):
        flag = 'grab_one_stack_done'
        self.command_reader.received_flags[flag] = False
        self.command_writer.grab_one_stack()
        self.command_reader.wait_for_received_flag(flag)

    def uncage(self, roi_x, roi_y):
        flag = 'uncaging_done'
        self.command_reader.received_flags[flag] = False
        self.command_writer.do_uncaging(roi_x, roi_y)
        self.command_reader.wait_for_received_flag(flag)

    def set_scan_shift(self, x, y):
        scan_shift_fast, scan_shift_slow = self.xy_to_scan_angle(x, y)
        flag = 'scan_angle_x_y'
        self.command_reader.received_flags[flag] = False
        self.command_writer.set_scan_shift(scan_shift_fast, scan_shift_slow)
        self.command_reader.wait_for_received_flag(flag)

    def set_z_slice_num(self, z_slice_num):
        flag = 'z_slice_num'
        self.command_reader.received_flags[flag] = False
        self.command_writer.set_z_slice_num(z_slice_num)
        self.command_reader.wait_for_received_flag(flag)

    def xy_to_scan_angle(self, x, y):
        scan_angle_multiplier = np.array(self.settings.get('scan_angle_multiplier'))
        scan_angle_range_reference = np.array(self.settings.get('scan_angle_range_reference'))
        fov = np.array(self.settings['fov_x_y'])
        # convert x and y to relative pixel coordinates
        x_center, y_center, _ = self.session.state.center_coordinates.get_motor_coordinates()
        fs_coordinates = np.array([x - x_center, y - y_center])
        fs_normalized = fs_coordinates / fov
        fs_angular = fs_normalized * scan_angle_multiplier * scan_angle_range_reference
        scan_shift_fast, scan_shift_slow = fs_angular
        # TODO: Add setting to invert scan shift. Or just tune it automatically.
        return scan_shift_fast, -scan_shift_slow

    def scan_angle_to_xy(self, scan_angle_x_y, x_center=None, y_center=None):
        scan_angle_multiplier = np.array(self.settings.get('scan_angle_multiplier'))
        scan_angle_range_reference = np.array(self.settings.get('scan_angle_range_reference'))
        fov = np.array(self.settings['fov_x_y'])
        fs_angular = np.array([scan_angle_x_y[0], -scan_angle_x_y[1]])
        if x_center is None:
            x_center, y_center, _ = self.session.state.center_coordinates.get_motor_coordinates()
        fs_normalized = fs_angular / (scan_angle_multiplier * scan_angle_range_reference)
        fs_coordinates = fs_normalized * fov
        x, y = fs_coordinates + np.array([x_center, y_center])
        return x, y

    def get_scan_props(self):
        flag = 'scanAngleMultiplier'
        self.command_reader.received_flags[flag] = False
        self.command_writer.get_scan_angle_multiplier()
        self.command_reader.wait_for_received_flag(flag)

        flag = 'scanAngleRangeReference'
        self.command_reader.received_flags[flag] = False
        self.command_writer.get_scan_angle_range_reference()
        self.command_reader.wait_for_received_flag(flag)

    def set_zoom(self, zoom):
        flag = 'zoom'
        self.command_reader.received_flags[flag] = False
        self.command_writer.set_zoom(zoom)
        self.command_reader.wait_for_received_flag(flag)
        self.settings.set('current_zoom', zoom)

    def set_resolution(self, x_resolution, y_resolution):
        flag = 'x_y_resolution'
        self.command_reader.received_flags[flag] = False
        self.command_writer.set_x_y_resolution(x_resolution, y_resolution)
        self.command_reader.wait_for_received_flag(flag)

    def set_macro_imaging_conditions(self):
        zoom = self.settings.get('macro_zoom')
        x_resolution = self.settings.get('macro_resolution_x')
        y_resolution = self.settings.get('macro_resolution_y')
        z_slice_num = self.settings.get('macro_z_slices')
        self.set_zoom(zoom)
        self.set_resolution(x_resolution, y_resolution)
        self.set_z_slice_num(z_slice_num)

    def set_normal_imaging_conditions(self):
        zoom = self.settings.get('imaging_zoom')
        x_resolution = self.settings.get('normal_resolution_x')
        y_resolution = self.settings.get('normal_resolution_y')
        z_slice_num = self.settings.get('imaging_slices')
        self.set_zoom(zoom)
        self.set_resolution(x_resolution, y_resolution)
        self.set_z_slice_num(z_slice_num)

    def set_reference_imaging_conditions(self):
        zoom = self.settings.get('reference_zoom')
        x_resolution = self.settings.get('normal_resolution_x')
        y_resolution = self.settings.get('normal_resolution_y')
        z_slice_num = self.settings.get('reference_slices')
        self.set_zoom(zoom)
        self.set_resolution(x_resolution, y_resolution)
        self.set_z_slice_num(z_slice_num)

    # TODO: Coordinates should be in their own class, combining motor and scan angle together.
    def get_current_position(self):
        flag = 'current_positions'
        self.command_reader.received_flags[flag] = False
        self.command_writer.get_current_motor_position()
        self.command_reader.wait_for_received_flag(flag)
        # x, y, z = self.session.current_coordinates.get_motor_coordinates()
        flag = 'scan_angle_x_y'
        self.command_reader.received_flags[flag] = False
        self.command_writer.get_scan_angle_xy()
        self.command_reader.wait_for_received_flag(flag)
        # current_scan_angle_x_y = self.settings.get('current_scan_angle_x_y')
        # x_with_scan_shift, y_with_scan_shift = self.scan_angle_to_xy(current_scan_angle_x_y, x_center=x, y_center=y)
        # self.settings.set('current_combined_coordinates', x_with_scan_shift, y_with_scan_shift, z)


if __name__ == "__main__":
    app = SpineTracker(sys.argv[1:])
    try:
        app.mainloop()
    except(KeyboardInterrupt, SystemExit):
        raise
