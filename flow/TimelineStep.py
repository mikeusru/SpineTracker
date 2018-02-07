class TimelineStep(dict):

    def __init__(self, step_name, imaging_or_uncaging, exclusive, period, duration, index=None, pos_id=None):
        super(TimelineStep, self).__init__()
        self['step_name'] = step_name
        self['imaging_or_uncaging'] = imaging_or_uncaging
        self['exclusive'] = exclusive
        self['period'] = period
        self['duration'] = duration
        self['index'] = index
        self['pos_id'] = pos_id

    def get_coordinates(self, positions):
        pos_id = self['pos_id']
        x, y, z = [positions[pos_id][xyz] for xyz in ['x', 'y', 'z']]
        return x, y, z
