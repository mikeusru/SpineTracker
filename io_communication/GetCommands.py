import os
import numpy as np

class GetCommands(object):
    def __init__(self, controller, file_path, *args, **kwargs):
        self.controller = controller
        self.instructions = controller.instructions
        self.file_path = file_path
        self.receivedFlags = {}
        self.args = args
        self.kwargs = kwargs
        if not os.path.isfile(self.file_path):
            open(self.file_path, 'a').close()

    def read_new_instructions(self, *args):
        inst_len = len(self.instructions)
        """read every line, see if there's new stuff to be had"""
        with open(self.file_path) as f:
            content = f.readlines()
            content = [x.strip() for x in content]
        ii = 0
        for line in content:
            if len(line) > 0:
                ii += 1
            if ii > inst_len:
                if self.controller.settings.get('verbose'):
                    print('\nnew line {0}\n'.format(ii))
                    print('\nnew instructions received\n')
                    print('\n{0}\n'.format(line))
                self.instructions.append(line)
                self.controller.instructions_in_queue.put(line)  # add to queue to handle lots of stuff to do
        """once file is read, run everything from queue"""
        """i guess i already have a second loop so this is redundant but whatever"""
        while not self.controller.instructions_in_queue.empty():
            line = self.controller.instructions_in_queue.get()
            self.translate_input_code(line)

    def translate_input_code(self, line):

        def check_num_args(total_args, min_args, max_args):
            if total_args is None:
                len_args = 0
            else:
                len_args = len(total_args)
            if min_args <= len_args <= max_args:
                return True
            else:
                print('Error - Missing arguments. Expected between {0} and {1}. Got {2}'.format(min_args, max_args,
                                                                                                len_args))
                return False

        # split command and arguments by comma
        line_parts = line.split(',')
        command = line_parts[0]
        # make command lowercase to avoid errors
        command = command.lower()
        if len(line_parts) > 1:
            args = line_parts[1:]
        else:
            args = []

        if command == 'stagemovedone':
            check_num_args(args, 3, 3)
            x, y, z = [float(args[xyz]) for xyz in [0, 1, 2]]
            if self.controller.settings.get('verbose'):
                print('\nStage Moved to x= {0} , y = {1}, z = {2}\n'.format(x, y, z))
            self.receivedFlags['stageMoveDone'] = True
        elif command == 'grabonestackdone':
            # commands need to be separated by commas, not spaces, otherwise file paths will cause problems
            check_num_args(args, 1, 1)
            self.controller.image_file_path = args[0]
            self.receivedFlags['grabOneStackDone'] = True
        elif command == 'currentposition':
            check_num_args(args, 3, 3)
            x, y, z = [float(args[xyz]) for xyz in [0, 1, 2]]
            self.controller.settings.set('current_coordinates', [x, y, z])
            self.receivedFlags['currentPosition'] = True
        elif command == 'uncagingdone':
            check_num_args(args, 0, 0)
            self.receivedFlags['uncagingDone'] = True
        elif command == 'fovXY_um':
            check_num_args(args, 2, 2)
            fov_x_y = np.array([float(args[XY]) for XY in [0, 1]])
            self.controller.settings['fov_x_y'] = fov_x_y
            self.receivedFlags['fovXY'] = True
        elif command == 'zoom':
            check_num_args(args, 1, 1)
            self.controller.settings.set('current_zoom', args[0])
            self.receivedFlags['zoom'] = True
        elif command == 'scananglexy':
            check_num_args(args, 2, 2)
            self.controller.settings.set('current_scan_angle_x_y', np.array([float(args[0]), float(args[1])]))
            self.receivedFlags['scanAngleXY'] = True
        elif command == 'scananglemultiplier':
            check_num_args(args, 2, 2)
            self.controller.settings.set('scan_angle_multiplier',np.array([float(args[0]), float(args[1])]))
            self.receivedFlags['scanAngleMultiplier'] = True
        elif command == 'scananglerangereference':
            check_num_args(args, 2, 2)
            self.controller.settings.set('scan_angle_range_reference',np.array([float(args[0]), float(args[1])]))
            self.receivedFlags['scanAngleRangeReference'] = True
        elif command == 'zslicenum':
            check_num_args(args, 1, 1)
            self.controller.settings.set('z_slice_num', args[0])
            self.receivedFlags['z_slice_num'] = True
        elif command == 'x_y_resolution':
            check_num_args(args, 2, 2)
            self.controller.settings.set('x_y_resolution', [args[0], args[1]])
            self.receivedFlags['x_y_resolution'] = True
        else:
            print("COMMAND NOT UNDERSTOOD")

    def wait_for_received_flag(self, flag):
        self.controller.print_status('Waiting for {0}'.format(flag))
        while True:
            self.controller.update()
            if self.receivedFlags[flag]:
                self.controller.print_status('{0} received'.format(flag))
                break
