import os
from queue import Queue

from interfaces.python.WriterToSpineTracker import WriterToSpineTracker


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
        self.command_interpreter.run_current_command()


class CommandInterpreter:

    def __init__(self):
        self.current_command = ''
        self.current_args = []
        self.command_dict = {}
        self.command_to_spine_tracker = WriterToSpineTracker()

    def interpret(self, line):
        line_parts = line.split(',')
        self.current_command = line_parts[0].lower()
        self.current_args = line_parts[1:]

    def run_current_command(self):
        self.command_dict[self.current_command].run(self.current_args)

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
        self.add_command('setzslicenum', 1, 1, self.set_z_slice_num)
        self.add_command('setxyresolution', 2, 2, self.set_x_y_resolution)
        self.add_command('getxyresolution', 0, 0, self.get_x_y_resolution)

    def add_command(self, name, min_args, max_args, fxn):
        self.command_dict[name] = SpineTrackerCommand(name, min_args, max_args, fxn)

    def move_x_y_z(self, args):
        x, y, z = [float(arg) for arg in args]
        # TODO: Move to new position
        self.command_to_spine_tracker.send_command('SetMotorPositionDone', x, y, z)

    def grab_one_stack(self, args):
        x, y, z = [float(arg) for arg in args]
        # TODO: Grab Stack
        save_path = 'path to tiff which was just saved'
        self.command_to_spine_tracker.send_command('AcquisitionDone', save_path)

    def set_zoom(self, args):
        zoom = float(args[0])
        # TODO: Set Zoom
        self.command_to_spine_tracker.send_command('Zoom', zoom)

    def run_uncaging(self, args):
        # TODO: Run Uncaging
        self.command_to_spine_tracker.send_command('UncagingDone')

    def get_current_position(self, args):
        # TODO: Get Current MOTOR coordinates
        x = 0
        y = 0
        z = 0
        self.command_to_spine_tracker.send_command('CurrentPosition', x, y, z)

    def get_fov_x_y(self, args):
        # TODO: Get the full field of view in µm...
        # This is not necessary and can be set in SpineTracker manually.
        x = 250
        y = 250
        self.command_to_spine_tracker.send_command('fov_XY_um', x, y)

    def get_scan_angle_x_y(self, args):
        # TODO: Get Galvo Scan Angles
        scan_shift_fast = 0
        scan_shift_slow = 0
        self.command_to_spine_tracker.send_command('ScanAngleXY',
                                                   scan_shift_fast,
                                                   scan_shift_slow)

    def get_scan_angle_multiplier(self, args):
        # TODO: Get Scan Angle Multiplier
        scan_angle_multiplier_fast = 1
        scan_angle_multiplier_slow = 1
        self.command_to_spine_tracker.send_command('ScanAngleMultiplier',
                                                   scan_angle_multiplier_fast,
                                                   scan_angle_multiplier_slow)

    def get_scan_angle_range_reference(self, args):
        # TODO: Get Scan Angle Multiplier
        scan_angle_range_reference_fast = 15
        scan_angle_range_reference_slow = 15
        self.command_to_spine_tracker.send_command('ScanAngleRangeReference',
                                                   scan_angle_range_reference_fast,
                                                   scan_angle_range_reference_slow)

    def set_scan_angle_x_y(self, args):
        scan_shift_fast, scan_shift_slow = [float(arg) for arg in args]
        # TODO: Set scan angle
        # respond with get scan angle command
        self.get_scan_angle_x_y([scan_shift_fast, scan_shift_slow])

    def set_z_slice_num(self, args):
        num_z_slices = int(args[0])
        # TODO: Set number of z slices
        self.command_to_spine_tracker.send_command('ZSliceNum', num_z_slices)

    def set_x_y_resolution(self, args):
        pixels_per_line, lines_per_frame = [int(arg) for arg in args]
        # TODO: Set imaging resolution
        # respond with get_x_y_resolution
        self.get_x_y_resolution(None)

    def get_x_y_resolution(self, args):
        # TODO: get imaging resolution
        pixels_per_line = 128
        lines_per_frame = 128
        self.command_to_spine_tracker.send_command('x_y_resolution', pixels_per_line, lines_per_frame)


class SpineTrackerCommand:

    def __init__(self, name, min_args, max_args, fxn):
        self.name = name
        self.min_args = min_args
        self.max_args = max_args
        self.function = fxn

    def run(self, args):
        if not self.check_num_args(args):
            return
        self.function(args)

    def check_num_args(self, args):
        if args is None:
            len_args = 0
        else:
            len_args = len(args)
        if self.min_args <= len_args <= self.max_args:
            return True
        else:
            print(f'Error - Missing arguments. Expected between {self.min_args} and {self.max_args}. Got {len_args}')
            return False
