import threading


class PositionTimer(object):
    def __init__(self, controller, steps, fun, *args, **kwargs):
        self.controller = controller
        self._timer = None
        self.steps = steps
        self.function = fun
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.stepCount = 0

        self.runTimes = []
        for step in self.steps:
            self.runTimes.append(step['startTime'])

        self.start()

    def _run(self, step_count):
        self.is_running = False
        self.start()  # starts next timer countdown before running function
        self.function(self.steps[step_count], *self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            if self.stepCount >= len(self.runTimes):
                return
            if self.stepCount == 0:
                prev_time = 0
            else:
                prev_time = self.runTimes[self.stepCount - 1]
            interval = self.runTimes[self.stepCount] - prev_time
            step_count = self.stepCount
            self.stepCount += 1
            # for now, interval is store in minutes. probably a good idea to change it to seconds.
            interval = interval * 60
            self.controller.print_status('\nTimer Interval = {0}'.format(interval))
            self._timer = threading.Timer(interval, self._run, args=[step_count])
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
