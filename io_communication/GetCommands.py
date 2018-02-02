import os


class GetCommands(object):
    def __init__(self, controller, filepath, *args, **kwargs):
        self.controller = controller
        self.instructions = controller.instructions
        self.filepath = filepath
        self.receivedFlags = {}
        if not os.path.isfile(self.filepath):
            open(self.filepath, 'a').close()

    def readNewInstructions(self, *args, **kwargs):
        instLen = len(self.instructions)
        """read every line, see if there's new stuff to be had"""
        with open(self.filepath) as f:
            content = f.readlines()
            content = [x.strip() for x in content]
        ii = 0
        for line in content:
            if len(line) > 0:
                ii += 1
            if ii > instLen:
                if self.controller.get_app_param('verbose'):
                    print('\nnew line {0}\n'.format(ii))
                    print('\nnew instructions received\n')
                    print('\n{0}\n'.format(line))
                self.instructions.append(line)
                self.controller.instructions_in_queue.put(line)  # add to queue to handle lots of stuff to do
        """once file is read, run everything from queue"""
        """i guess i already have a second loop so this is redundant but whatever"""
        while not self.controller.instructions_in_queue.empty():
            line = self.controller.instructions_in_queue.get()
            self.translateInputCode(line)

    def translateInputCode(self, line):

        def checkNumArgs(args, minArgs, maxArgs):
            if args == None:
                lenArgs = 0
            else:
                lenArgs = len(args)
            if minArgs <= lenArgs <= maxArgs:
                return (True)
            else:
                print('Error - Missing arguments. Expected between {0} and {1}. Got {2}'.format(minArgs, maxArgs,
                                                                                                lenArgs))
                return (False)

        # split command and arguments by comma
        lineParts = line.split(',')
        command = lineParts[0]
        # make command lowercase to avoid errors
        command = command.lower()
        if len(lineParts) > 1:
            args = lineParts[1:]
        else:
            args = []

        if command == 'stagemovedone':
            checkNumArgs(args, 3, 3)
            x, y, z = [float(args[xyz]) for xyz in [0, 1, 2]]
            if self.controller.get_app_param('verbose'):
                print('\nStage Moved to x= {0} , y = {1}, z = {2}\n'.format(x, y, z))
            self.receivedFlags['stageMoveDone'] = True
        elif command == 'grabonestackdone':
            # commands need to be separated by commas, not spaces, otherwise file paths will cause problems
            checkNumArgs(args, 1, 1)
            self.controller.imageFilePath = args[0]
            self.receivedFlags['grabOneStackDone'] = True
        elif command == 'currentposition':
            checkNumArgs(args, 3, 3)
            x, y, z = [float(args[xyz]) for xyz in [0, 1, 2]]
            self.controller.currentCoordinates = [x, y, z]
            self.receivedFlags['currentPosition'] = True
        elif command == 'uncagingdone':
            checkNumArgs(args, 0, 0)
            self.receivedFlags['UncagingDone'] = True
        elif command == 'fovXY_um':
            checkNumArgs(args, 2, 2)
            X, Y = [float(args[XY]) for XY in [0, 1]]
            self.controller.settings['fovXY'] = [X, Y]
            self.receivedFlags['fovXY'] = True
        elif command == 'zoom':
            checkNumArgs(args, 1, 1)
            self.controller.acq['currentZoom'] = float(args[0])
            self.receivedFlags['zoom'] = True
        elif command == 'scananglexy':
            checkNumArgs(args, 2, 2)
            self.controller.currentScanAngleXY = (float(args[0]), float(args[1]))
            self.receivedFlags['scanAngleXY'] = True
        elif command == 'scananglemultiplier':
            checkNumArgs(args, 2, 2)
            self.controller.scanAngleMultiplier = (float(args[0]), float(args[1]))
            self.receivedFlags['scanAngleMultiplier'] = True
        elif command == 'scananglerangereference':
            checkNumArgs(args, 2, 2)
            self.controller.scanAngleRangeReference = (float(args[0]), float(args[1]))
            self.receivedFlags['scanAngleRangeReference'] = True
        elif command == 'zslicenum':
            checkNumArgs(args, 1, 1)
            self.controller.acq['z_slice_num'] = float(args[0])
            self.receivedFlags['z_slice_num'] = True
        else:
            print("COMMAND NOT UNDERSTOOD")

    def waitForReceivedFlag(self, flag):
        self.controller.print_status('Waiting for {0}'.format(flag))
        while True:
            self.controller.update()
            if self.receivedFlags[flag]:
                self.controller.print_status('{0} received'.format(flag))
                break
