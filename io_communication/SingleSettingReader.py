class SingleSettingReader:

    def __init__(self):
        self.min_args = 0
        self.max_args = 0
        self.pipe_command = ''
        self.settings_name = None
        self.received_flag = False
        self.received_function = None
        self.received_args = []
        self.setting_target = None
        self.logger = None

    def set_setting_target(self, fun):
        self.setting_target = fun

    def set_logger(self, fun):
        self.logger = fun

    def run_fxn(self):
        if self.received_function is not None:
            self.received_function(self.received_args)

    def update_setting(self):
        if self.settings_name is not None:
            self.setting_target(self.settings_name, self.received_args)

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
            self.logger(
                f'Error - Incorrect number of arguments for {self.pipe_command}.'
                f' Expected between {self.min_args} and {self.max_args}. Got {len_args}')
            return False