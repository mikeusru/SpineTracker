import numpy as np

from app.utilities.math_helpers import blank_to_zero, none_to_blank


class Setting:

    def __init__(self, name, gui_var, saved, default, callback=None, dtype=None):
        self.name = name
        self.gui_var = gui_var
        self.saved = saved
        self.default = default
        self.value = None
        self.callback = callback
        self.dtype = dtype

        self.set(self.default)
        self.update_gui()
        self.set_trace()

    def _update_dtype(self):
        if self.dtype is not None:
            self.value = blank_to_zero(self.value)
            if self.value is not None:
                if self.dtype == str:
                    self.value = ''.join(self.value)
                else:
                    try:
                        self.value = np.array([self.value], dtype=self.dtype).squeeze()
                    except ValueError as err:
                        self.value = np.array(0, dtype=self.dtype)
                        print(err)

    def set(self, value):
        self.value = value
        self._update_dtype()
        self.update_gui()

    def get_value(self):
        val = self.value
        if (type(self.value) is np.ndarray) and (self.value.size == 1):
            val = self.value.item(0)
        return val

    def update_gui(self):
        if self.gui_var is not None:
            # print('var: {}, value: {}'.format(self.gui_var, self.value))
            value = none_to_blank(self.get_value())
            self.gui_var.set(value)

    def set_trace(self, callback=None):
        if callback is not None:
            self.callback = callback
        if (self.gui_var is not None) and (self.callback is not None):
            self.gui_var.trace_add('write', self.callback)

    def update_value_from_gui(self):
        self.value = self.gui_var.get()
        self._update_dtype()

    def needs_default_trace(self):
        if (self.gui_var is not None) and (self.callback is None):
            return True
        else:
            return False