import os
from queue import Queue

import numpy as np


class FLIMageEventHandler:

    def __init__(self, file_to_imaging_software, file_to_spine_tracker):
        self.file_to_read = file_to_imaging_software
        self.file_to_write = file_to_spine_tracker
        self.instructions_received = []
        self.instructions_to_run = Queue()
        self.command_interpreter = CommandInterpreter()
        self._create_file_to_read()

    def _create_file_to_read(self):
        if not os.path.isfile(self.file_to_read):
            open(self.file_to_read, 'a').close()

    def read_new_commands(self, *args):
        content = self._read_file()
        self._check_for_new_commands(content)
        self._run_new_commands()

    def _read_file(self):
        with open(self.file_to_read) as file:
            content = file.readlines()
            content = [line.strip() for line in content]
            return content

    def _check_for_new_commands(self, content):
        instructions_length = len(self.instructions_received)
        for count, line in enumerate(content):
            if count >= instructions_length:
                self._add_line_to_instructions(line)

    def _add_line_to_instructions(self, line):
        self.instructions_received.append(line)
        self.instructions_to_run.put(line)

    def _run_new_commands(self):
        while not self.instructions_to_run.empty():
            line = self.instructions_to_run.get()
            self.interpret_line(line)

    def interpret_line(self, line):

        self.command_interpreter.interpret(line)

        def check_num_args(total_args, min_args, max_args):
            if total_args is None:
                len_args = 0
            else:
                len_args = len(total_args)
            if min_args <= len_args <= max_args:
                return True
            else:
                print(f'Error - Missing arguments. Expected between {min_args} and {max_args}. Got {len_args}')
                return False


class CommandInterpreter:

    def __init__(self):
        self.current_command = ''
        self.current_args = []
        self.command_dict = {}

    def interpret(self, line):
        line_parts = line.split(',')
        self.command = line_parts[0].lower()
        self.args = line_parts[1:]

    def initialize_commands(self):
        self.add_command('movexyz', 3, 3, self.move_x_y_z)
        self.add_command('grabonestack', 0, 0, self.grab_one_stack)
        self.add_command('setzoom', 1, 1, self.set_zoom)
        self.add_command('rununcaging', 0, 0, self.run_uncaging)
        self.add_command('getcurrentposition', 0, 0, self.get_current_position)
        self.add_command('getfov_xy', 0, 0, self.get_fov_x_y)
        self.add_command('getscananglexy', 0, 0, self.get_scan_angle_x_y)
        self.add_command('getscananglemultiplier', 0, 0, self.get_scan_angle_multiplier)
        self.add_command('getscananglerangereference', 0, 0, self.get_scan_angle_range_reference)
        self.add_command('setscananglexy', 2, 2, self.set_scan_angle_x_y)
        self.add_command('setscananglexy', 2, 2, self.set_scan_angle_x_y)
        self.add_command('setzslicenum', 1, 1, self.set_z_slice_num)
        self.add_command('setxyresolution', 2, 2, self.set_x_y_resolution)
        self.add_command('getxyresolution', 0, 0, self.get_x_y_resolution)

    def add_command(self, name, min_args, max_args, function):
        self.command_dict[name] = SpineTrackerCommand(name, min_args, max_args, function)

    def move_x_y_z(self):
        pass


class SpineTrackerCommand:

    def __init__(self, name, min_args, max_args, function):
        self.name = name
        self.min_args = min_args
        self.max_args = max_args
        self.function = function
