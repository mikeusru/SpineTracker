import os
from queue import Queue

from app.MainGuiBuilder import MainGuiBuilder
from app.inherited.inherited.inherited.SpineTrackerSettings import SettingsManager, CommandLineInterpreter
from io_communication.CommandReader import CommandReader
from io_communication.CommandWriter import CommandWriter
from io_communication.file_listeners import InstructionThread


class Initializer:

    def __init__(self, *args, **kwargs):
        self.args = args
        self.settings = self.initialize_settings()
        self.command_line_interpreter = self.initialize_command_line_interpreter()
        self.gui = self.initialize_guis()
        self.communication = self.initialize_communication()

    def initialize_settings(self):
        settings = SettingsManager(self)
        settings.initialize_settings()
        return settings

    def initialize_guis(self):
        return MainGuiBuilder(self.settings)

    def initialize_command_line_interpreter(self):
        command_line_interpreter = CommandLineInterpreter(self.settings, self.args)
        command_line_interpreter.interpret()
        return command_line_interpreter

    def initialize_communication(self):
        return Communication(self.settings)


class Communication:

    def __init__(self, settings):
        self.settings = settings
        self.instructions_received = []
        self.instructions_in_queue = Queue()
        self.command_writer = CommandWriter(self.settings)
        self.command_reader = CommandReader(self.settings, self.instructions_in_queue, self.instructions_received)
        self.instructions_listener_thread = self.initialize_instructions_listener_thread()

    def initialize_instructions_listener_thread(self):
        input_file = self.settings.get('input_file')
        path, filename = os.path.split(input_file)
        read_function = self.command_reader.read_new_commands
        with self.instructions_in_queue.mutex:
            self.instructions_in_queue.queue.clear()
            instructions_listener_thread = InstructionThread(self, path, filename, read_function)
            instructions_listener_thread.start()
        return instructions_listener_thread
