import threading
import time


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
        self.run_intervals = []
        for step in self.steps:
            self.run_times.append(step['start_time'])
            self.run_intervals.append(step['end_time'] - step['start_time'])
        self.start()

    def _run(self, step_count):
        self.is_running = False
        self.start()  # starts next timer countdown before running function
        self.function(self.steps[step_count], self.pos_id, *self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            if self.step_count >= len(self.run_times):
                return
            # if self.step_count == 0:
            # prev_time = 0
            # else:
            # prev_time = self.run_times[self.step_count - 1]
            if self.step_count == 0:
                interval = 0
            else:
                interval = self.run_intervals[self.step_count - 1]
            step_count = self.step_count
            self.step_count += 1
            print(f'\nTimer Interval = {round(interval)}s')
            self._timer = threading.Timer(interval, self._run, args=[step_count])
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


class ExperimentTimer:

    def __init__(self, steps, fun, *args, **kwargs):
        self._timer = None
        self.steps = steps
        self.function = fun
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
        self.function(self.steps[step_count], *self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            if self.step_count >= len(self.run_times):
                return
            if self.step_count == 0:
                interval = 0
            else:
                interval = self.run_times[self.step_count] - self.run_times[self.step_count - 1]
            step_count = self.step_count
            self.step_count += 1
            print(f'\nTimer Interval = {round(interval)}s')
            self._timer = threading.Timer(interval, self._run, args=[step_count])
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


class DisplayTimer:
    def __init__(self, interval, settings):
        self.settings = settings
        self._timer = None
        self.interval = interval
        self.is_running = False
        self.start_time = time.time()
        self.timenow = 0
        self.settings.set('display_timer', '{0:02}:{1:02}'.format(0, 0))

    def _run(self):
        self.is_running = False
        self.start(False)
        self.timenow = time.time() - self.start_time
        # print('time = {0}'.format(self.timenow))
        timemin = int(self.timenow / 60.0)
        timesec = int(self.timenow - timemin * 60)
        try:
            self.settings.set('display_timer', '{0:02}:{1:02}'.format(timemin, timesec))
        except:
            self.stop()

    def start(self, reset=True):
        if not self.is_running:
            self._timer = threading.Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True
            if reset:
                self.start_time = time.time()

    def stop(self):
        if self.is_running:
            self._timer.cancel()
            self.is_running = False
