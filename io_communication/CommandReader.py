import os
import numpy as np


class CommandReader:
    def __init__(self, session, instructions_in_queue, instructions_received):
        self.session = session
        self.settings = session.settings
        self.instructions_in_queue = instructions_in_queue
        self.instructions_received = instructions_received
        self.received_flags = {}
        self.file_path = self.settings.get('input_file')
        if not os.path.isfile(self.file_path):
            open(self.file_path, 'a').close()

    def read_new_commands(self, *args):
        content = self._read_file()
        self._check_for_new_commands(content)
        self._run_new_commands()

    def _read_file(self):
        with open(self.file_path) as file:
            content = file.readlines()
            content = [line.strip() for line in content]
            return content

    def _check_for_new_commands(self, content):
        instructions_length = len(self.instructions_received)
        for count, line in enumerate(content):
            if count >= instructions_length:
                if self.settings.get('verbose'):
                    print('\nnew line {0}\n'.format(count))
                    print('\nnew instructions received\n')
                    print('\n{0}\n'.format(line))
                self._add_line_to_instructions(line)

    def _add_line_to_instructions(self, line):
        self.instructions_received.append(line)
        self.instructions_in_queue.put(line)

    def _run_new_commands(self):
        while not self.instructions_in_queue.empty():
            line = self.instructions_in_queue.get()
            self.interpret_line(line)

    def interpret_line(self, line):

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

        def get_command_and_args(line):
            line_parts = line.split(',')
            command = line_parts[0].lower()
            args = line_parts[1:]
            return command, args

        command, args = get_command_and_args(line)

        # TODO: There's definitely some design pattern to make this better
        if command == 'stagemovedone':
            check_num_args(args, 3, 3)
            x, y, z = [float(args[xyz]) for xyz in [0, 1, 2]]
            if self.settings.get('verbose'):
                print('\nStage Moved to x= {0} , y = {1}, z = {2}\n'.format(x, y, z))
            self.received_flags['stage_move_done'] = True
        elif command == 'grabonestackdone':
            # commands need to be separated by commas, not spaces, otherwise file paths will cause problems
            check_num_args(args, 1, 1)
            self.settings.set('image_file_path', args[0])
            self.received_flags['grab_one_stack_done'] = True
        elif command == 'currentposition':
            check_num_args(args, 3, 3)
            x, y, z = [float(args[xyz]) for xyz in [0, 1, 2]]
            self.session.state.current_coordinates.set_motor(x, y, z)
            self.received_flags['current_positions'] = True
        elif command == 'uncagingdone':
            check_num_args(args, 0, 0)
            self.received_flags['uncaging_done'] = True
        elif command == 'fovXY_um':
            check_num_args(args, 2, 2)
            self.settings.set('fov_x', args[0])
            self.settings.set('fov_y', args[1])
            self.received_flags['fovXY'] = True
        elif command == 'zoom':
            check_num_args(args, 1, 1)
            self.settings.set('current_zoom', args[0])
            self.received_flags['zoom'] = True
        elif command == 'scananglexy':
            check_num_args(args, 2, 2)
            self.session.state.current_coordinates.set_scan_angles_x_y(args[0], args[1])
            self.received_flags['scan_angle_x_y'] = True
        elif command == 'scananglemultiplier':
            check_num_args(args, 2, 2)
            self.settings.set('scan_angle_multiplier', np.array([float(args[0]), float(args[1])]))
            self.received_flags['scanAngleMultiplier'] = True
        elif command == 'scananglerangereference':
            check_num_args(args, 2, 2)
            self.settings.set('scan_angle_range_reference', np.array([float(args[0]), float(args[1])]))
            self.received_flags['scanAngleRangeReference'] = True
        elif command == 'zslicenum':
            check_num_args(args, 1, 1)
            self.settings.set('z_slice_num', args[0])
            self.received_flags['z_slice_num'] = True
        elif command == 'x_y_resolution':
            check_num_args(args, 2, 2)
            self.settings.set('x_y_resolution', [args[0], args[1]])
            self.received_flags['x_y_resolution'] = True
        else:
            print("COMMAND NOT UNDERSTOOD")

    def wait_for_received_flag(self, flag):
        # self.controller.print_status('Waiting for {0}'.format(flag))
        print('Waiting for {0}'.format(flag))
        while True:
            self.session.prevent_freezing_during_loops()
            if self.received_flags[flag]:
                # self.controller.print_status('{0} received'.format(flag))
                print('{0} received'.format(flag))
                break
