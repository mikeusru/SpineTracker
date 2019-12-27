from tkinter import ttk
from tkinter.filedialog import askopenfilename
import os
from app.Timeline import TimelineStepBlock


class TimelineStepsFrame(ttk.Frame):
    def __init__(self, container):
        ttk.Frame.__init__(self, container)
        self.container = container
        self.gui = self.build_gui_items()

    def build_gui_items(self):
        gui = dict()
        gui['image_radio_button'] = ttk.Radiobutton(self, text='Image',
                                                    variable=self.container.gui_vars['image_or_uncage'],
                                                    value='Image')
        gui['image_radio_button'].grid(row=0, column=0, pady=10, padx=10)
        gui['uncage_radio_button'] = ttk.Radiobutton(self, text='Uncage',
                                                     variable=self.container.gui_vars['image_or_uncage'],
                                                     value='Uncage')
        gui['uncage_radio_button'].grid(row=0, column=1, padx=10, pady=10)
        gui['step_name_label'] = ttk.Label(self, text='Step Name:', font=self.container.settings['large_font'])
        gui['step_name_label'].grid(row=1, column=0, sticky='nw', padx=10, pady=3)
        gui['step_name_entry'] = ttk.Entry(self, width=30,
                                           textvariable=self.container.gui_vars['step_name'])
        gui['step_name_entry'].grid(row=1, column=1, sticky='nw', padx=10, pady=3)
        gui['period_label1'] = ttk.Label(self, text='Period: ',
                                         font=self.container.settings['large_font'])
        gui['period_label1'].grid(row=2, column=0, sticky='nw', padx=10, pady=3)
        gui['period_entry_frame'] = ttk.Frame(self)
        gui['period_entry_frame'].grid(row=2, column=1, sticky='nw', padx=10, pady=3)
        gui['period_entry'] = ttk.Entry(gui['period_entry_frame'], width=4,
                                        textvariable=self.container.gui_vars['period'])
        gui['period_entry'].grid(row=0, column=0, sticky='nw', padx=0, pady=0)
        gui['period_label2'] = ttk.Label(gui['period_entry_frame'], text='sec',
                                         font=self.container.settings['large_font'])
        gui['period_label2'].grid(row=0, column=1, sticky='nw', padx=0, pady=0)
        gui['iterations_label1'] = ttk.Label(self, text='Iterations: ',
                                             font=self.container.settings['large_font'])
        gui['iterations_label1'].grid(row=3, column=0, sticky='nw', padx=10, pady=3)
        gui['iterations_entry'] = ttk.Entry(self, width=4,
                                            textvariable=self.container.gui_vars['iterations'])
        gui['iterations_entry'].grid(row=3, column=1, sticky='nw', padx=10, pady=3)
        gui['exclusive_checkbutton'] = ttk.Checkbutton(self, text='Exclusive',
                                                       variable=self.container.gui_vars['exclusive'])
        gui['exclusive_checkbutton'].grid(row=4, column=0, sticky='nw', padx=10, pady=3)
        gui['uncaging_checkbutton'] = ttk.Checkbutton(self, text='Uncaging While Imaging',
                                                      variable=self.container.gui_vars['uncaging_while_imaging'])
        gui['uncaging_checkbutton'].grid(row=4, column=1, sticky='nw', padx=10, pady=3)
        gui['custom_command_label1'] = ttk.Label(self, text='Custom Command: ',
                                                 font=self.container.settings['large_font'])
        gui['custom_command_label1'].grid(row=5, column=0, sticky='nw', padx=10, pady=3)
        gui['custom_command_entry'] = ttk.Entry(self, width=30,
                                                textvariable=self.container.gui_vars['custom_command'])
        gui['custom_command_entry'].grid(row=5, column=1, sticky='nw', padx=10, pady=3)
        gui['settings_file_frame'] = ttk.Frame(self)
        gui['settings_file_frame'].grid(row=6, column=0, sticky='sw', columnspan=2)

        gui['setting_file_label1'] = ttk.Label(gui['settings_file_frame'], text='Setting File: ',
                                                 font=self.container.settings['large_font'])
        gui['setting_file_label1'].grid(row=0, column=0, sticky='nw', padx=10, pady=3)
        gui['settings_file_button'] = ttk.Button(gui['settings_file_frame'], text="...", command=self.get_imaging_settings_file)
        gui['settings_file_button'].grid(row=0, column=1, padx=5, pady=0, sticky='wn')
        gui['setting_file_entry'] = ttk.Entry(gui['settings_file_frame'], width=30,
                                                textvariable=self.container.gui_vars['imaging_settings_file'])
        gui['setting_file_entry'].grid(row=0, column=2, sticky='nw', padx=10, pady=3)
        gui['add_step_button'] = ttk.Button(self, text="Add Step", command=self.add_step_callback)
        gui['add_step_button'].grid(row=7, column=0, padx=10, pady=10, sticky='wn')

        gui['update_step_button'] = ttk.Button(self, text="Update selected", command=self.update_step_callback)
        gui['update_step_button'].grid(row=7, column=1, padx=10, pady=10, sticky='wn')
        gui['stagger_frame'] = ttk.Frame(self)
        gui['stagger_frame'].grid(row=8, column=0, sticky='sw', columnspan=2)
        gui['stagger_label1'] = ttk.Label(gui['stagger_frame'], text='Stagger: ',
                                          font=self.container.settings['large_font'])
        gui['stagger_label1'].grid(row=0, column=0, sticky='nw', padx=10, pady=10)

        gui['stagger_entry'] = ttk.Entry(gui['stagger_frame'], width=4,
                                         textvariable=self.container.gui_vars['stagger'])
        gui['stagger_entry'].grid(row=0, column=1, sticky='nw', padx=0, pady=10)
        gui['stagger_label2'] = ttk.Label(gui['stagger_frame'], text='min',
                                          font=self.container.settings['large_font'])
        gui['stagger_label2'].grid(row=0, column=2, sticky='nw', padx=0, pady=10)
        return gui

    def get_imaging_settings_file(self):
        path = askopenfilename(initialdir=os.path.expanduser(""),
                               title="Select Imaging Settings File")
        self.container.gui_vars['imaging_settings_file'].set(path)

    def add_step_callback(self, ind=None, *args):
        timeline_step = TimelineStepBlock()
        for key in timeline_step:
            timeline_step[key] = self.container.get_setting(key)
        self.uncaging_specific_setting(timeline_step)
        timeline_step['index'] = ind
        if not timeline_step.is_valid():
            print('Warning - Period and Iterations must both be >0 for Imaging Steps')
            return
        self.container.timeline.add_timeline_step(timeline_step)
        self.container.draw_timeline_steps_general()
        self.container.timeline.backup_timeline()

    def update_step_callback(self):
        tree = self.container.gui['timeline_tree']
        item_number = None
        if len(tree.selection()) == 0:
            return
        for item in tree.selection():
            item_number = tree.index(item)
        ts = self.container.timeline.timeline_steps[item_number]
        for key in ts:
            ts[key] = self.container.get_setting(key)
        self.uncaging_specific_setting(ts)
        self.container.draw_timeline_steps_general()
        self.container.timeline.backup_timeline()
        children = tree.get_children()
        n = len(children)  ###Ryohei need to correct.
        if n > 0 & item_number < n:
            tree.selection_set(children[item_number])

    @staticmethod
    def uncaging_specific_setting(timeline_steps):
        if timeline_steps['image_or_uncage'] == 'Uncage':
            timeline_steps['iterations'] = 1
            # timeline_steps['exclusive'] = True

    def download_from_timeline_step(self, timeline_step):
        for key in timeline_step:
            self.container.events['set_setting'](key, timeline_step[key])

    def image_uncage_radiobutton_switch(self):
        var = self.container.gui_vars['image_or_uncage'].get()
        if var == "Image":
            self.container.events['set_setting']('exclusive', False)
            self.gui['uncaging_checkbutton'].config(state='normal')
            self.gui['exclusive_checkbutton'].config(state='normal')
            self.gui['iterations_entry'].config(state='normal')
        else:
            self.container.events['set_setting']('exclusive', True)
            self.container.events['set_setting']('uncaging_while_imaging', False)
            self.gui['uncaging_checkbutton'].config(state='disabled')
            self.gui['exclusive_checkbutton'].config(state='disabled')
            self.gui['iterations_entry'].config(state='disabled')

    def uncaging_while_imaging_checkbutton_on(self):
        uncaging_while_imaging = self.container.gui_vars['uncaging_while_imaging'].get()
        if uncaging_while_imaging:
            self.container.events['set_setting']('exclusive', True)
            self.gui['exclusive_checkbutton'].config(state='disabled')
            self.gui['exclusive_checkbutton'].config(state='disabled')
        else:
            self.gui['exclusive_checkbutton'].config(state='enabled')


