import os

from io_communication.CommandReader_pipe import remove_spaces
from io_communication.file_listeners import FileReaderThread


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