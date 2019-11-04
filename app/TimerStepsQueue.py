import copy
import datetime as dt
from queue import Queue, Empty


class TimerStepsQueue(Queue):

    def __init__(self):
        super(TimerStepsQueue, self).__init__()
        self.current_step = None

    def add_step(self, step):
        single_step = copy.copy(step)  # .copy() returns dict, not TimelineStepBlock object
        self.put(single_step)

    def load_next_step(self):
        self.current_step = self.get()
        self.print_current_step_info()

    def print_current_step_info(self):
        single_step = self.current_step
        pos_id = self.current_step.get('pos_id')
        if single_step.get('exclusive'):
            ex = 'Exclusive'
        else:
            ex = 'Non-Exclusive'
        print('{0} {1} Timer {2} running at {3}:{4}:{5} '.format(ex, single_step['image_or_uncage'], pos_id,
                                                                 dt.datetime.now().hour, dt.datetime.now().minute,
                                                                 dt.datetime.now().second))

    def clear_timers(self):
        while not self.empty():
            try:
                self.get(False)
            except Empty:
                continue