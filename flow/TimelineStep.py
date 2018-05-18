class TimelineStep(dict):
    """Whole Timeline Steps"""
    def __init__(self, step_name, imaging_or_uncaging, exclusive, period=60, duration=1,
                 start_time=None, end_time=None, index=None, pos_id=None):
        super(TimelineStep, self).__init__()
        self['step_name'] = step_name
        self['imaging_or_uncaging'] = imaging_or_uncaging
        self['exclusive'] = exclusive
        self['period'] = period
        self['duration'] = duration
        self['index'] = index
        self['pos_id'] = pos_id
        self['start_time'] = start_time
        self['end_time'] = end_time

    # def __copy__(self):
    #     newone = type(self)()
    #     newone.__dict__.update(self.__dict__)
    #     return newone

    def get_coordinates(self, positions):
        pos_id = self['pos_id']
        x, y, z = [positions[pos_id][xyz] for xyz in ['x', 'y', 'z']]
        return x, y, z

class MiniTimelineStep(TimelineStep):
    """Individual steps on the timeline chart"""
    def __init__(self, timeline_step, start_time, end_time):
        super(TimelineStep, self.__init__(timeline_step.step_name,
                                          timeline_step.imaging_or_uncaging,
                                          timeline_step.exclusive))
        self['start_time'] = start_time
        self['end_time'] = end_time