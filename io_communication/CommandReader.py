import os
import re

from io_communication.file_listeners import FileReaderThread


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


class CommandReader:
    def __init__(self, session, instructions_in_queue):
        self.session = session
        self.settings = session.settings
        self.instructions_in_queue = instructions_in_queue
        self.instructions_received = []
        self.received_flags = {}
        self.read_settings = {}
        self.create_read_settings()
        self.file_path = self.settings.get('input_file')
        self.imaging_param_file = self.settings.get('imaging_param_file') #Added by Ryohei
        if not os.path.isfile(self.file_path):
            open(self.file_path, 'a').close()

    def reset(self):
        self.instructions_received = []

    def create_read_settings(self):
        self.new_setting('stagemovedone', 3, 3, None, None)
        self.new_setting('acquisitiondone', 0, 0, None, None)
        self.new_setting('intensityfilepath', 1, 1, 'image_file_path', None)
        self.new_setting('currentposition', 3, 3, None, self.set_current_position)
        self.new_setting('uncagingdone', 0, 0, None, None)
        self.new_setting('intensitysaving', 1, 1, 'intensity_saving', None)
        self.new_setting('fovxyum', 2, 2, None, self.set_fov_x_y_um)
        self.new_setting('zoom', 1, 1, 'current_zoom', None)
        self.new_setting('scanvoltagexy', 2, 2, None, self.set_scan_voltages_x_y)
        self.new_setting('scanvoltagemultiplier', 2, 2, 'scan_voltage_multiplier', None)
        self.new_setting('scanvoltagerangereference', 2, 2, 'scan_voltage_range_reference', None)
        self.new_setting('zslicenum', 1, 1, 'z_slice_num', None)
        self.new_setting('resolutionxy', 2, 2, 'resolution_x_y', None)
        self.new_setting('customcommandreceived', 0, 0, None, None)
        self.new_setting('parameterfilesaved', 1, 1, None, None) #Added for future use by Ryohei. You have to take filepath here.
        self.new_setting('rotation', 1, 1, 'rotation', None) #Rotation is necessary for drift correction. Need to implement.
        self.new_setting('zstep', 1, 1, 'zstep', None) #Required for correcting drift.
        self.new_setting('channelstobesaved', 1, 1, None, None)  # Added for future use by Ryohei

    def set_current_position(self, args):
        x, y, z = args
        self.session.state.current_coordinates.set_motor(x, y, z)
        #self.print_line('\nStage Moved to x= {0} , y = {1}, z = {2}\n'.format(x, y, z))

    def set_scan_voltages_x_y(self, args):
        x, y = args
        self.session.state.current_coordinates.set_scan_voltages_x_y(x, y)

    def set_fov_x_y_um(self, args):
        fov_x, fov_y = args
        self.settings.set('fov_x', fov_x)
        self.settings.set('fov_y', fov_y)

    def new_setting(self, text_file_command, min_args, max_args, settings_name, received_function):
        new_setting = SingleSettingReader(self.session)
        new_setting.min_args = min_args
        new_setting.max_args = max_args
        new_setting.text_file_command = text_file_command
        new_setting.settings_name = settings_name
        new_setting.received_function = received_function
        self.read_settings[text_file_command] = new_setting

    def read_new_commands(self, *args):
        content = self._read_file()
        self._check_for_reset(content)
        self._check_for_new_commands(content)
        self._run_new_commands()

    def read_imaging_param_file(self): #Added by Ryohei. Listener is perhaps not necessary.
        with open(self.imaging_param_file, 'rt') as file:
            content = file.readlines()
            for count, line in enumerate(content):
                self.interpret_line(line)

    def _read_file(self):
        with open(self.file_path, 'r') as file:
            content = file.readlines()
            content = [remove_spaces(line) for line in content]
            return content

    def _check_for_reset(self, content):
        if len(content) < len(self.instructions_received):
            self.reset()

    def _check_for_new_commands(self, content):
        instructions_length = len(self.instructions_received)
        for count, line in enumerate(content):
            if count >= instructions_length:
                if self.settings.get('verbose'):
                    self.print_line('\nnew line {0}\n'.format(count))
                    self.print_line('\nnew instructions received\n')
                    self.print_line('\n{0}\n'.format(line))
                self._add_line_to_instructions(line)

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

    def set_response(self, text_file_command):
        self.read_settings[text_file_command].waiting()

    def wait_for_response(self, text_file_command):
        self.print_line('Waiting for {0}'.format(text_file_command))
        while True:
            self.session.prevent_freezing_during_loops()
            if self.read_settings[text_file_command].is_done():
                self.print_line('{0} received'.format(text_file_command))
                break

    def print_line(self, line):
        self.session.print_to_log(line)


class ImagingParamFileHandler:

    def __init__(self):
        self.session = None
        self.settings = None
        self.file_path = None
        self.content = None
        self.listener_thread = None

    def init_session(self, session):
        self.session = session
        self.settings = session.settings
        self.file_path = self.settings.get('imaging_param_file')

    def create_listener_thread(self):
        path, filename = os.path.split(self.file_path)
        self.listener_thread = FileReaderThread(self, path, filename, self.read_file)
        self.listener_thread.start()

    def read_file(self, *args):
        with open(self.file_path, 'r') as file:
            content = file.readlines()
            content = [remove_spaces(line) for line in content]
            self.content = content
        self._record_params()

    def _record_params(self):
        for line in self.content:
            self.session.communication.command_reader.interpret_line(line)


class SingleSettingReader:

    def __init__(self, session):
        self.session = session
        self.min_args = 0
        self.max_args = 0
        self.text_file_command = ''
        self.settings_name = None
        self.received_flag = False
        self.received_function = None
        self.received_args = []

    def run_fxn(self):
        if self.received_function is not None:
            self.received_function(self.received_args)

    def update_setting(self):
        if self.settings_name is not None:
            self.session.settings.set(self.settings_name, self.received_args)

    def waiting(self):
        self.received_flag = False

    def is_done(self):
        return self.received_flag

    def set(self, args):
        self.received_args = args
        self.verify_arg_num()
        self.received_flag = True
        self.update_setting()
        self.run_fxn()

    def verify_arg_num(self):
        if self.received_args is None:
            len_args = 0
        else:
            len_args = len(self.received_args)
        if self.min_args <= len_args <= self.max_args:
            return True
        else:
            self.session.print_to_log(
                f'Error - Incorrect number of arguments for {self.text_file_command}.'
                f' Expected between {self.min_args} and {self.max_args}. Got {len_args}')
            return False
