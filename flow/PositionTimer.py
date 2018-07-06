import threading


class PositionTimer(object):
    def __init__(self, session, steps, fun, pos_id, *args, **kwargs):
        self.session = session
        self._timer = None
        self.steps = steps
        self.function = fun
        self.pos_id = pos_id
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.step_count = 0

        self.run_times = []
        for step in self.steps:
            self.run_times.append(step['start_time'])

        self.start()

    def _run(self, step_count):
        self.is_running = False
        self.start()  # starts next timer countdown before running function
        self.function(self.steps[step_count], self.pos_id, *self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            if self.step_count >= len(self.run_times):
                return
            if self.step_count == 0:
                prev_time = 0
            else:
                prev_time = self.run_times[self.step_count - 1]
            interval = self.run_times[self.step_count] - prev_time
            step_count = self.step_count
            self.step_count += 1
            # for now, interval is store in minutes. probably a good idea to change it to seconds.
            interval = interval * 60
            print(f'\nTimer Interval = {round(interval)}s')
            self._timer = threading.Timer(interval, self._run, args=[step_count])
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
