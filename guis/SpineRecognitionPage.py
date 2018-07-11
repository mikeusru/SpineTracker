import tkinter as tk
from tkinter.filedialog import askdirectory
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
        gui['training_data_folder_preview_entry'] = ttk.Entry(self, text=self.get_truncated_var('training_data_path'),
                                                              state='disabled')
        gui['training_data_folder_preview_entry'].grid(row=0, column=1, padx=10, pady=10, sticky='nw')

        return gui

    def select_training_data(self):
        path = askdirectory(initialdir="../",
                            title="Choose a directory.")
        self.session.settings.set('training_data_path', path)
        self.gui['training_data_folder_preview_entry'].config(text=self.get_truncated_var('training_data_path'))

    def get_truncated_var(self, var):
        return self.session.settings.get(var)[-10:]
