import os
import re

from app.io_communication.CommandHandler import CommandHandler
from app.io_communication.Event import Event
from app.io_communication.SingleSettingReader import SingleSettingReader


def remove_spaces(line):
    line = line.strip()
    remove_space_after_comma = re.compile('(, )')
    return remove_space_after_comma.sub(',', line)


def get_command_and_args(line):
    line_parts = line.split(',')
    line_parts = [remove_spaces(part) for part in line_parts]
    command = line_parts[0].lower()
    args = line_parts[1:]
    return command, args


class CommandReader(CommandHandler):
    def __init__(self, instructions_in_queue):
        super().__init__()
        self.instructions_in_queue = instructions_in_queue
        self.instructions_received = []
        self.received_flags = {}
        self.read_settings = {}
        self.stage_control_target = Event()
        self.scan_voltage_target = Event()
        self.setting_target = Event()
        self.freeze_preventer = Event()
        self.fov_target = Event()

    def reset(self):
        self.instructions_received = []

    def create_read_settings(self):
        self.new_setting('setmotorpositiondone', 3, 3, None, None)
        self.new_setting('acquisitiondone', 0, 0, None, None)
        self.new_setting('intensityfilepath', 1, 1, 'image_file_path', None)
        self.new_setting('currentposition', 3, 3, None, self.set_current_position)
        self.new_setting('uncagingdone', 0, 0, None, None)
        self.new_setting('uncaging processed.', 0, 0, None, None)
        self.new_setting('uncaginglocation', 2, 2, None, None)
        self.new_setting('intensitysaving', 1, 1, 'intensity_saving', None)
        self.new_setting('fovxyum', 2, 2, None, self.set_fov_x_y_um)
        self.new_setting('zoom', 1, 1, 'current_zoom', None)
        self.new_setting('scanvoltagexy', 2, 2, None, self.set_scan_voltages_x_y)
        self.new_setting('scanvoltagemultiplier', 2, 2, 'scan_voltage_multiplier', None)
        self.new_setting('scanvoltagerangereference', 2, 2, 'scan_voltage_range_reference', None)
        self.new_setting('zslicenum', 1, 1, 'z_slice_num', None)
        self.new_setting('resolutionxy', 2, 2, 'resolution_x_y', None)
        self.new_setting('customcommandreceived', 0, 0, None, None)
        self.new_setting('loadsettings processed.', 0, 0, None, None)
        self.new_setting('parameterfilesaved', 1, 1, None,
                         None)  # Added for future use by Ryohei. You have to take filepath here.
        self.new_setting('rotation', 1, 1, 'rotation',
                         None)  # Rotation is necessary for drift correction. Need to implement.
        self.new_setting('zstep', 1, 1, 'zstep', None)  # Required for correcting drift.
        self.new_setting('channelstobesaved', 1, 1, None, None)  # Added for future use by Ryohei

    def set_current_position(self, args):
        x, y, z = args
        self.stage_control_target(x, y, z)

    def set_scan_voltages_x_y(self, args):
        x, y = args
        self.scan_voltage_target(x, y)

    def set_fov_x_y_um(self, args):
        fov_x, fov_y = args
        self.fov_target(fov_x, fov_y)

    def new_setting(self, pipe_command, min_args, max_args, settings_name, received_function):
        new_setting = SingleSettingReader()
        new_setting.setting_target += self.setting_target
        new_setting.logger += self.logger
        new_setting.min_args = min_args
        new_setting.max_args = max_args
        new_setting.pipe_command = pipe_command
        new_setting.settings_name = settings_name
        new_setting.received_function = received_function
        self.read_settings[pipe_command] = new_setting

    def read_new_command(self, message):
        self.print_received_command(message)
        self._add_line_to_instructions(message)
        self._run_new_commands()

    def print_received_command(self, message):
        self.command_target(message)

    def _add_line_to_instructions(self, line):
        self.instructions_received.append(line)
        self.instructions_in_queue.put(line)

    def _run_new_commands(self):
        while not self.instructions_in_queue.empty():
            line = self.instructions_in_queue.get()
            self.interpret_line(line)

    def interpret_line(self, line):
        command, args = get_command_and_args(line)
        if command in self.read_settings.keys():
            self.read_settings[command].set(args)
        else:
            self.print_line(f"COMMAND NOT UNDERSTOOD: {command}")

    def set_response(self, pipe_command):
        self.read_settings[pipe_command].waiting()

    def wait_for_response(self, pipe_command):
        self.print_line('Waiting for {0}'.format(pipe_command))
        while True:
            self.prevent_freeze()
            if self.read_settings[pipe_command].is_done():
                self.print_line('{0} received'.format(pipe_command))
                break

    def prevent_freeze(self):
        self.freeze_preventer()

    def print_line(self, line):
        self.logger(line)
