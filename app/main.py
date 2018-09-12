import copy
import datetime as dt
import os
import sys
import threading
from queue import Queue

from app.AcquiredImage import AcquiredImage, ReferenceImage, MacroImage
from app.Communication import Communication
from app.Coordinates import Coordinates
from app.MainGuiBuilder import MainGuiBuilder
from app.Positions import Positions
from app.Timeline import Timeline
from app.settings import SettingsManager, CommandLineInterpreter
from flow.PositionTimer import PositionTimer, DisplayTimer
from spine_yolo.spine_yolo import SpineYolo
from spine_yolo.yolo_argparser import YoloArgparse

class State:
    def __init__(self, session):
        self.session = session
        self.settings = session.settings
        self.step_running = False
        self.imaging_active = False
        self.current_pos_id = 1
        self.current_coordinates = Coordinates()
        self.center_coordinates = Coordinates()
        self.current_image = AcquiredImage()
        self.ref_image = ReferenceImage()
        self.ref_image_zoomed_out = ReferenceImage()
        self.macro_image = MacroImage()
        self.position_timers = {}
        self.display_timer = DisplayTimer(1.0, self.settings)
        self.queue_run = None

    def clear_position_timers(self):
        self.position_timers = {}

    def initialize_position_timers(self, individual_steps):
        self.clear_position_timers()
        for pos_id in individual_steps:
            self.position_timers[pos_id] = PositionTimer(self, individual_steps[pos_id],
                                                         self.session.add_step_to_queue, pos_id)


class SpineTracker:
    def __init__(self, *args):
        self.gui = MainGuiBuilder(self)
        self.settings = SettingsManager(self.gui)
        self.args = args
        self.command_line_interpreter = self.initialize_command_line_interpreter()
        self.communication = Communication(self)
        self.positions = self.initialize_positions()
        self.timeline = Timeline(self)
        self.gui.build_guis()
        self.timer_steps_queue = TimerStepsQueue()
        self.state = State(self)
        self.settings.initialize_gui_callbacks()
        self.initialize_init_directory()
        self.log_file = open('log.txt', 'w')
        self.yolo = SpineYolo(YoloArgparse().parse_args())
        self.update_center_position() #Ryohei: Necessary to calculate center from data stored in position.p.

    def exit(self):
        self.stop_imaging()
        print('quitting')
        self.communication.instructions_listener_thread.stop()
        print('Instruction listener closed')
#        self.communication.param_file_listener_thread.stop()
#        print('param file listener closed')
        self.log_file.close()
        self.gui.destroy()
        print('goodbye')

    def initialize_init_directory(self):
        init_directory = self.settings.get('init_directory')
        directory = os.path.dirname(init_directory)
        if not os.path.exists(directory):
            os.mkdir(directory)

    def initialize_command_line_interpreter(self):
        command_line_interpreter = CommandLineInterpreter(self.settings, self.args)
        command_line_interpreter.interpret()
        return command_line_interpreter

    def initialize_positions(self):
        positions = Positions(self)
        positions.load_previous_positions()
        return positions

    def mainloop(self):
        self.gui.mainloop()

    def start_expt_log(self):
        file_path = self.settings.get('experiment_log_file')
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.mkdir(directory)
        open(file_path, 'a').close()

    def write_to_expt_log(self, line):
        file_path = self.settings.get('experiment_log_file')
        with open(file_path, "a") as file:
            file.write(line + '\n')

    def load_image(self, image_type='standard'):
        pos_id = self.state.current_pos_id
        self.read_imaging_param_file(pos_id, True) #Ryohei. Before reading, make sure the current setting. Filename particularly.
        if image_type == 'standard':
            self.state.current_image.zoom = self.settings.get('imaging_zoom')
            self.state.current_image.load(self.settings, pos_id)
            self.gui.reset_figure_for_af_images(self.state.current_image)
        elif image_type == 'zoomed_out':
            self.state.current_image.zoom = self.settings.get('reference_zoom')
            self.state.current_image.load(self.settings, pos_id)
            self.gui.reset_figure_for_af_images(self.state.current_image)
        elif image_type == 'reference':
            self.state.ref_image.load(self.settings, pos_id)
            self.gui.reset_figure_for_af_images(self.state.ref_image)
        elif image_type == 'reference_zoomed_out':
            self.state.ref_image_zoomed_out.load(self.settings, pos_id)
            self.gui.reset_figure_for_af_images(self.state.ref_image_zoomed_out)
        elif image_type == 'macro':
            self.state.macro_image.load(self.settings, pos_id)
            self.state.macro_image.set_image_contrast()
            self.state.macro_image.create_pil_image()
        else:
            print("WRONG IMAGE TYPE")

    def correct_xyz_drift(self, pos_id=None, zoom=None):
        if zoom is None:
            zoom = self.settings.get('imaging_zoom')
        if pos_id is None:
            pos_id = self.positions.current_position
        reference_max_projection = self.get_ref_image(zoom, pos_id)
        self.state.current_image.calc_x_y_z_drift(reference_max_projection)
        self.positions.update_coordinates_for_drift(pos_id, self.state.current_image.drift_x_y_z)
        self.gui.show_drift_info(self.state.current_image, pos_id)
        self.positions.record_drift_history_of_acquired_image(self.state.current_image)
        self.positions.backup_positions()

    def update_center_position(self):
        xyz_average = self.positions.get_average_coordinate()
        self.state.center_coordinates.set_relative_to_center_coordinates(xyz_average['x'],xyz_average['y'], xyz_average['z'])
        self.positions.update_all_coordinates_relative_to_center()

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
        self.positions.current_position = pos_id
        self.gui.indicate_step_on_timeline(single_step)
        if single_step['image_or_uncage'] == 'Image':
            self.image_at_pos_id(pos_id)
            self.state.step_running = False
            self.load_image()
            self.correct_xyz_drift(pos_id)
        elif single_step['image_or_uncage'] == 'Uncage':
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
            self.gui.select_current_position_position_page_tree(pos_id) #Ryohei To see where you are looking at.
            self.communication.set_reference_imaging_conditions()
            self.image_at_pos_id(pos_id)
            self.load_image(image_type='zoomed_out')
            self.correct_xyz_drift(pos_id, zoom=self.settings.get('reference_zoom'))
            self.communication.set_normal_imaging_conditions()
            self.image_at_pos_id(pos_id)
            self.load_image(image_type='standard')
            self.correct_xyz_drift(pos_id, zoom=self.settings.get('imaging_zoom'))
            self.gui.select_current_position_position_page_tree(pos_id) #Upload acquired images?

    def record_imaging_to_log(self, pos_id):
        self.write_to_log('Position {}: {}'.format(pos_id, self.settings.get('image_file_path')))

    def record_uncaging_to_log(self, pos_id):
        self.write_to_log('Position {0}: Uncaging at {1}:{2}:{3}'.format(pos_id, dt.datetime.now().hour,
                                                                         dt.datetime.now().minute,
                                                                         dt.datetime.now().second))

    def create_new_position(self, take_new_refs=True):
        if take_new_refs:
            self.collect_new_reference_images()
            self.communication.get_motor_position()
        self.positions.create_new_pos(self.state.ref_image, self.state.ref_image_zoomed_out)
        self.update_center_position()
        self.gui.update_positions_table()
        self.positions.backup_positions()

    def clear_positions(self, *args):
        self.positions.clear()
        self.gui.update_positions_table()

    def remove_position(self, pos_id):
        self.positions.remove(pos_id)
        self.gui.update_positions_table()
        self.positions.backup_positions()

    def update_position(self, pos_id):
        self.communication.get_motor_position()
        new_coordinates = self.state.current_coordinates.copy()
        self.positions.set_coordinates(pos_id, new_coordinates)
        self.gui.update_positions_table()
        self.positions.backup_positions()

    def collect_new_reference_images(self):
        self.communication.set_reference_imaging_conditions() #Ryohei Note that before image acquisition, file name is not updated.
        self.communication.grab_stack()
        self.read_imaging_param_file(self.positions.current_position, False)
        self.load_image('reference_zoomed_out')
        self.communication.set_normal_imaging_conditions()
        self.communication.grab_stack()
        self.read_imaging_param_file(self.positions.current_position, True) #Import parameters only for normal imaging.
        self.load_image('reference')

    def read_imaging_param_file(self, pos_id=None, import_parameters_toposition=False):
        self.communication.command_reader.read_imaging_param_file()
        if pos_id is None:
            pos_id = self.positions.current_position
        if import_parameters_toposition:
            self.positions.import_parameters_from_session(pos_id)

    def collect_new_macro_image(self):
        self.communication.set_macro_imaging_conditions()
        self.communication.grab_stack()
        self.load_image('macro')

    def move_to_pos_id(self, pos_id):
        coordinates = self.positions.get_coordinates(pos_id)
        coordinates.update_to_center(self)
        self.communication.move_to_coordinates(coordinates)

    def write_to_log(self, line):
        file_path = self.settings.get('experiment_log_file')
        if os.path.exists(file_path):
            with open(file_path, "a") as f:
                f.write(line + '\n')

    def start_imaging(self):
        self.communication.set_normal_imaging_conditions()
        self.state.display_timer.start()
        self.start_expt_log()
        self.timer_steps_queue.clear_timers()
        individual_steps = self.timeline.get_steps_for_queue()
        self.state.initialize_position_timers(individual_steps)
        self.state.imaging_active = True
        self.state.queue_run = threading.Thread(target=self.run_steps_from_queue_when_appropriate)
        self.state.queue_run.daemon = True
        self.state.queue_run.start()

    def stop_imaging(self):
        for pos_id in self.state.position_timers:
            self.state.position_timers[pos_id].stop()
        self.state.imaging_active = False
        self.state.display_timer.stop()

    def train_yolo_model(self):
        self.yolo.toggle_training(True)
        self.yolo.set_data_path(self.settings.get('training_data_path'))
        self.yolo.set_classes()
        self.yolo.set_anchors()
        self.yolo.set_partition()
        self.yolo.set_model_save_path(self.settings.get('new_model_path'))
        self.yolo.run()

    def test_yolo_model(self):
        self.yolo.toggle_training(False)
        self.yolo.prepare_image_data(self.settings.get('test_data_path'))
        self.yolo.set_classes()
        self.yolo.set_anchors()
        self.yolo.set_dummy_partition()
        self.yolo.set_trained_model_path(self.settings.get('trained_model_path'))
        self.yolo.run()

    def test_yolo_on_single_image(self):
        image_path = self.settings.get('yolo_image_path')
        self.yolo.set_classes()
        self.yolo.set_anchors()
        self.yolo.set_trained_model_path(self.settings.get('trained_model_path'))
        self.yolo.run_on_single_image(image_path)

    def print_to_log(self, line):
        print(line)
        self.write_to_log(line)
        self.settings.set('communication_log', line)


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
        print('{0} {1} Timer {2} running at {3}:{4}:{5} '.format(ex, single_step['image_or_uncage'], pos_id,
                                                                 dt.datetime.now().hour, dt.datetime.now().minute,
                                                                 dt.datetime.now().second))

    def clear_timers(self):
        with self.mutex:
            self.queue.clear()


if __name__ == "__main__":
    app = SpineTracker(sys.argv[1:])
    try:
        app.mainloop()
    except(KeyboardInterrupt, SystemExit):
        raise
