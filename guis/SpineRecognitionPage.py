import tkinter as tk
from tkinter.filedialog import askdirectory, askopenfilename
from tkinter import ttk
import matplotlib

matplotlib.use("TkAgg")


class SpineRecognitionPage(ttk.Frame):
    name = 'SpineRecognition'

    def __init__(self, container, session):
        ttk.Frame.__init__(self, container)
        self.session = session
        self.gui = self.define_gui_elements()

    def define_gui_elements(self):
        settings = self.session.settings
        gui = dict()
        gui['select_training_data_button'] = tk.Button(self, text="Select Training Data",
                                                       font=settings.get('large_font'),
                                                       command=self.select_training_data)
        gui['select_training_data_button'].grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        gui['training_data_folder_preview_entry'] = ttk.Entry(self,
                                                              width=80,
                                                              textvariable=settings.get_gui_var('training_data_path'),
                                                              state='readonly',
                                                              justify='right')
        gui['training_data_folder_preview_entry'].grid(row=0, column=1, padx=10, pady=10, sticky='nw')
        gui['select_model_button'] = tk.Button(self, text="Select Model",
                                               font=settings.get('large_font'),
                                               command=self.select_model)
        gui['select_model_button'].grid(row=1, column=0, sticky='nw', padx=10, pady=10)
        gui['model_path_entry'] = ttk.Entry(self,
                                            width=80,
                                            textvariable=settings.get_gui_var('trained_model_path'),
                                            state='readonly',
                                            justify='right')
        gui['model_path_entry'].grid(row=1, column=1, padx=10, pady=10, sticky='nw')

        return gui

    def select_training_data(self):
        path = askdirectory(initialdir="../",
                            title="Choose a directory")
        self.session.settings.set('training_data_path', path)

    def select_model(self):
        path = askopenfilename(initialdir=self.session.settings.get('trained_model_path'),
                            title="Choose a pre-trained model")
        self.session.settings.set('trained_model_path', path)

    def put_cursor_at_end_of_path(self):
        self.gui['training_data_folder_preview_entry'].xview_moveto(1)
        self.gui['current_model_path_entry'].xview_moveto(1)

    def test_model(self):
        pass

    def train_model(self):
        pass

    def load_model(self):
        pass

