import pickle
import numpy as np
import os


class Timeline:

    def __init__(self, session):
        self.session = session
        self.settings = session.settings
        self.positions = session.positions
        self.timeline_steps = self.initialize_timeline_steps()
        self.ordered_timelines_by_positions = AllPositionTimelines(self.settings)

    def initialize_timeline_steps(self):
        file_name = self.settings.get('init_directory') + 'timeline_steps.p'
        try:
            timeline_steps = TimelineSteps(self.settings)
            if os.path.isfile(file_name):
                try:
                    timeline_steps_list = pickle.load(open(file_name, 'rb'))
                    for step in timeline_steps_list:
                        timeline_steps.add_step(step)
                except:
                    print('error in loading timeline_step.p file')

        except AttributeError as err:
            print(f'Unable to load {file_name}: {err}')
            timeline_steps = TimelineSteps(self.settings)
        return timeline_steps

    def backup_timeline(self):
        timeline_steps_list = [step for step in self.timeline_steps]
        pickle.dump(timeline_steps_list,
                    open(self.settings.get('init_directory') + 'timeline_steps.p', 'wb'))

    def build_full_timeline(self):
        self.ordered_timelines_by_positions = AllPositionTimelines(self.settings) #RYohei: It is necessary to renew this every time. `
        if self.check_if_steps_defined():
            self.populate_individual_timelines()
            self.ordered_timelines_by_positions.make_timelines_fit_together()

    def add_timeline_step(self, timeline_step):
        self.timeline_steps.add_step(timeline_step)

    def check_if_steps_defined(self):
        if len(self.timeline_steps) == 0:
            return False
        else:
            return True

    def get_pos_id_list(self):
        if len(self.positions) == 0:
            pos_id_list = list(range(1, 6))
        else:
            pos_id_list = [pos_id for pos_id in self.positions]
        return pos_id_list

    def populate_individual_timelines(self):
        pos_id_list = self.get_pos_id_list()
        self.ordered_timelines_by_positions.populate(pos_id_list)
        self.ordered_timelines_by_positions.initialize_steps(self.timeline_steps)

    def get_y_label_list(self):
        y_label_list = []
        for individual_position_timeline in self.ordered_timelines_by_positions.values():
            y_label_list.append(individual_position_timeline.y_label)
        return y_label_list

    def get_total_pos_num(self):
        total_pos_num = len(self.get_pos_id_list())
        return total_pos_num

    def get_steps_for_queue(self):
        steps_for_queue = self.ordered_timelines_by_positions.get_timeline_step_individual_list()
        return steps_for_queue


class AllPositionTimelines(dict):

    def __init__(self, settings):
        super(AllPositionTimelines, self).__init__()
        self.settings = settings

    def populate(self, pos_id_list):
        for pos_count, pos_id in enumerate(pos_id_list, 1):
            self.add_individual_position_timeline(pos_id, pos_count)

    def initialize_steps(self, timeline_steps):
        for pos_id in self:
            for step in timeline_steps:
                self[pos_id].add_step(step)

    def add_individual_position_timeline(self, pos_id, pos_count):
        self[pos_id] = IndividualPositionTimeline(pos_id, pos_count, self.settings)

    def make_timelines_fit_together(self):
        previous_step = None
        while True:
            individual_timeline_step = self.shift_next_individual_timeline_step(previous_step)
            previous_step = individual_timeline_step
            pos_id = individual_timeline_step['pos_id']
            self.update_all_min_start_times(individual_timeline_step)
            self[pos_id].step_building_index += 1
            if self.is_done_building():
                break

    def shift_next_individual_timeline_step(self, previous_step):
        next_individual_timeline_step, earliest_start_time = self.get_next_step_if_exclusive(previous_step)
        if next_individual_timeline_step is None:
            earliest_start_time = np.array(np.inf)
            next_individual_timeline_step = None
            for pos_id in self:
                if self[pos_id].is_empty():
                    continue
                individual_timeline_step, actual_start_time = self[
                    pos_id].get_next_step()
                if (actual_start_time < earliest_start_time) or (
                        actual_start_time == earliest_start_time and individual_timeline_step['exclusive']):
                    earliest_start_time = actual_start_time
                    next_individual_timeline_step = individual_timeline_step
        next_individual_timeline_step.shift_start_end_times(new_start_time=earliest_start_time)
        return next_individual_timeline_step

    def get_next_step_if_exclusive(self, previous_step):
        if previous_step is None:
            return None, None
        if previous_step['exclusive']:
            pos_id = previous_step['pos_id']
            if self[pos_id].is_empty():
                return None, None
            current_step, actual_start_time = self[pos_id].get_next_step()
            if current_step['exclusive']:
                return current_step, actual_start_time
        return None, None

    def update_all_min_start_times(self, individual_timeline_step):
        reference_pos_id = individual_timeline_step['pos_id']
        for pos_id in self:
            if (pos_id == reference_pos_id) or individual_timeline_step['exclusive']:
                new_min_time = individual_timeline_step['end_time']
            else:
                new_min_time = individual_timeline_step['start_time']
            self[pos_id].update_min_start_time(
                new_min_time)

    def is_done_building(self):
        done_building = True
        for individual_position_timeline in self.values():
            if not individual_position_timeline.is_empty():
                done_building = False
                break
        return done_building

    def get_timeline_step_individual_list(self):
        ordered_timeline_step_individual_list_by_position= {}
        for pos_id, individual_position_timeline in self.items():
            ordered_timeline_step_individual_list_by_position[pos_id] = individual_position_timeline.timeline_step_individual_list
        return ordered_timeline_step_individual_list_by_position


class IndividualPositionTimeline(dict):

    def __init__(self, pos_id, pos_count, settings):
        super(IndividualPositionTimeline, self).__init__()
        self.settings = settings
        self.stagger = self.settings.get('stagger')
        self.pos_id = pos_id
        self.y_label = ''
        self.total_time = 0
        self.pos_count = pos_count
        self.start_end_time_array = []
        self.timeline_step_individual_list = []
        self.min_start_time = 0
        self.step_building_index = 0
        self._set_y_label()

    def _set_y_label(self):
        self.y_label = 'Position {}'.format(self.pos_id)

    def add_step(self, step):
        """divide step into individual steps for each period"""
        start_time = self.total_time
        if start_time == 0:
            duration = step['iterations'] * step['period'] / 60 + self.stagger * (self.pos_count - 1)
        else:
            duration = step['iterations'] * step['period'] / 60
        period = step['period']
        start_end_time_list = self.calc_start_end_time(period, duration, start_time)
        timeline_step_individual = [
            TimelineStepsMini(step, start_end_time['start'], start_end_time['end'], self.pos_id) for
            start_end_time in start_end_time_list]
        self.timeline_step_individual_list += timeline_step_individual
        self.total_time += duration

    def calc_start_end_time(self, period, duration, start_time):
        """Create list of dicts with start and end times for each step"""
        start_times_single_step = self.calc_start_times(period, duration, start_time)
        end_times_single_step = self.calc_end_times(start_times_single_step, period)
        start_end_time_list = [{'start': start, 'end': end} for start, end in
                               zip(start_times_single_step, end_times_single_step)]
        # start_end_single_step = np.array([start_times_single_step, end_times_single_step])
        return start_end_time_list

    def calc_start_times(self, period, duration, start_time):
        start_time_array = np.arange(start_time, start_time + duration, period / 60)
        return start_time_array

    def calc_end_times(self, start_times, period):
        end_times = start_times + period / 60
        return end_times

    def get_next_step(self):
        individual_step = self.timeline_step_individual_list[self.step_building_index]
        actual_start_time = max(individual_step['start_time'], self.min_start_time)
        # add small amount of time based on position so they are added to the queue sequentially, not at the same time
        actual_start_time = actual_start_time + (self.pos_count * 0.001)
        return individual_step, actual_start_time

    def update_min_start_time(self, start_time):
        self.min_start_time = np.max([self.min_start_time, start_time])

    def is_empty(self):
        if self.step_building_index >= len(self.timeline_step_individual_list):
            return True
        else:
            return False


class TimelineSteps(list):

    def __init__(self, settings):
        super(TimelineSteps, self).__init__()
        self.settings = settings

    def add_step(self, timeline_step):
        index = timeline_step.get('index')
        if index is None:
            self.append(timeline_step)
        else:
            self.insert(index, timeline_step)


class TimelineStepBlock(dict):
    def __init__(self, step_name='Step1', image_or_uncage='Image', exclusive=True, period=60, iterations=1,
                 start_time=None, end_time=None, index=None, pos_id=None):
        super(TimelineStepBlock, self).__init__()
        if (iterations is None) or (iterations == 0):
            iterations = 1
        if (period is None) or (period == 0):
            period = 60
        self['step_name'] = step_name
        self['image_or_uncage'] = image_or_uncage
        self['exclusive'] = exclusive
        self['period'] = period
        self['iterations'] = iterations
        self['index'] = index
        self['pos_id'] = pos_id
        self['start_time'] = start_time
        self['end_time'] = end_time

    def is_valid(self):
        if (self['period']*self['iterations'] == 0) and (self['image_or_uncage'] == 'Image'):
            return False
        else:
            return True

    def shift_start_end_times(self, new_start_time):
        time_shift = new_start_time - self['start_time']
        self['start_time'] += time_shift
        self['end_time'] += time_shift


class TimelineStepsMini(TimelineStepBlock):
    """Individual steps on the timeline chart"""

    def __init__(self, timeline_step, start_time, end_time, pos_id):
        super().__init__(timeline_step['step_name'],
                         timeline_step['image_or_uncage'],
                         timeline_step['exclusive'],
                         start_time=start_time,
                         end_time=end_time,
                         pos_id=pos_id)
