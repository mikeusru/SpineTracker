from io_communication.Event import Event


class CommandHandler:
    def __init__(self):
        self.logger = Event()
        self.command_target = Event()