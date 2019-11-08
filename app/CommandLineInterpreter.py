import getopt
import sys


class CommandLineInterpreter:

    def __init__(self, settings_manager, *args):
        self.settings_manager = settings_manager
        self.args = args

    def interpret(self):
        args = self.args
        if args is not None:
            args = args[0][0]
            if len(args) != 0:
                try:
                    options, remainder = getopt.getopt(args, 'sv', ['simulation', 'verbose'])
                except getopt.GetoptError:
                    print('Error - incorrect input format')
                    print('correct Format: main.py -v -s')
                    sys.exit(2)
                for opt, val in options:
                    if opt in ('-s', '--simulation'):
                        print('simulation mode on')
                        self._set_setting('simulation', True)
                    elif opt in ('-v', '--verbose'):
                        print('verbose mode on')
                        self._set_setting('verbose', True)

    def _set_setting(self, name, value):
        self.settings_manager.set(name, value)