from operator import itemgetter

from app.AcquiredImage import AcquiredImage, ReferenceImage, MacroImage
from app.Coordinates import Coordinates
from flow.PositionTimer import DisplayTimer, ExperimentTimer


class State:
    def __init__(self, session):
        self.session = session
        self.settings = session.settings
        self.step_running = False
        self.imaging_active = False
        self.current_pos_id = 1
        self.center_coordinates = Coordinates()
        self.center_coordinates.settings_reader += self.settings.get
        self.center_coordinates.center_motor_reader += self.center_coordinates.get_motor
        self.current_coordinates = self.center_coordinates.copy()
        self.current_image = AcquiredImage()
        self.ref_image = ReferenceImage()
        self.ref_image_zoomed_out = ReferenceImage()
        self.macro_image = MacroImage()
        self.position_timers = {}
        self.experiment_timer = None
        self.display_timer = DisplayTimer(1.0, self.settings)
        self.queue_run = None
        self.log_file = None

    def initialize_position_timers(self, individual_steps):
        self.position_timers = {}
        all_steps = []
        for pos_id in individual_steps:
            all_steps += individual_steps[pos_id]
        all_steps_sorted = sorted(all_steps, key=itemgetter('start_time', 'pos_id'))
        self.experiment_timer = ExperimentTimer(all_steps_sorted, self.session.add_step_to_queue)
        # for pos_id in all_positions:
        #     self.position_timers[pos_id] = PositionTimer(self, individual_steps[pos_id],
        #                                                  self.session.add_step_to_queue, pos_id)