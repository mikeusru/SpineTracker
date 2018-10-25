import tkinter as tk
from tkinter.filedialog import askdirectory, askopenfilename
from tkinter import ttk
import matplotlib

matplotlib.use("TkAgg")


class SpineRecognitionPage(ttk.Frame):
    name = 'Spine Recognition'

    def __init__(self, container, session):
        ttk.Frame.__init__(self, container)
        self.session = session
        self.gui = self.define_gui_elements()

    def define_gui_elements(self):
        settings = self.session.settings
        gui = dict()
        gui['training_data_folder_label'] = tk.Label(self, text="Training Data Folder:",
                                                     font=settings.get('large_font'))
        gui['training_data_folder_label'].grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        gui['select_training_data_button'] = tk.Button(self, text="...",
                                                       font=settings.get('normal_font'),
                                                       command=self.select_training_data)
        gui['select_training_data_button'].grid(row=0, column=2, sticky='nw', padx=10, pady=10)
        gui['training_data_folder_preview_entry'] = ttk.Entry(self,
                                                              width=80,
                                                              textvariable=settings.get_gui_var('training_data_path'),
                                                              state='readonly')
        gui['training_data_folder_preview_entry'].grid(row=0, column=1, padx=10, pady=10, sticky='nw')
        gui['model_path_label'] = tk.Label(self, text="Trained Model File:",
                                           font=settings.get('large_font'))
        gui['model_path_label'].grid(row=1, column=0, sticky='nw', padx=10, pady=10)
        gui['select_model_button'] = tk.Button(self, text="...",
                                               font=settings.get('normal_font'),
                                               command=self.select_model)
        gui['select_model_button'].grid(row=1, column=2, sticky='nw', padx=10, pady=10)
        gui['model_path_entry'] = ttk.Entry(self,
                                            width=80,
                                            textvariable=settings.get_gui_var('trained_model_path'),
                                            state='readonly')
        gui['model_path_entry'].grid(row=1, column=1, padx=10, pady=10, sticky='nw')
        gui['train_model_button'] = tk.Button(self, text='Train Model',
                                              font=settings.get('large_font'),
                                              command=self.train_model)
        gui['train_model_button'].grid(row=3, column=0, sticky='nw', padx=10, pady=10)
        gui['test_model_button'] = tk.Button(self, text='Test Model',
                                             font=settings.get('large_font'),
                                             command=self.test_model)
        gui['test_model_button'].grid(row=3, column=1, sticky='nw', padx=10, pady=10)
        gui['run_on_single_image_button'] = tk.Button(self, text='Run On Single Image',
                                             font=settings.get('large_font'),
                                             command=self.test_single_image)
        gui['run_on_single_image_button'].grid(row=4, column=0, sticky='nw', padx=10, pady=10)

        return gui

    def select_training_data(self):
        path = askdirectory(initialdir=self.session.settings.get('training_data_path'),
                            title="Choose a directory")
        self.set_new_path('training_data_path', path)

    def select_model(self):
        path = askopenfilename(initialdir=self.session.settings.get('trained_model_path'),
                               title="Choose a pre-trained model")
        self.set_new_path('trained_model_path', path)

    def select_image_file(self):
        path = askopenfilename(initialdir=self.session.settings.get('trained_model_path'),
                               title="Choose a pre-trained model")
        self.session.settings.set('yolo_image_path', path)

    def put_cursor_at_end_of_path(self):
        self.gui['training_data_folder_preview_entry'].xview_moveto(1)
        self.gui['model_path_entry'].xview_moveto(1)

    def test_model(self):
        self.select_folder_for_test_data()
        self.session.test_yolo_model()

    def test_single_image(self):
        self.select_image_file()
        self.session.test_yolo_on_single_image()

    def train_model(self):
        self.select_folder_for_newly_trained_model()
        self.session.train_yolo_model()
        # self.session.train_yolo_model_with_different_sized_datasets()

    def select_folder_for_newly_trained_model(self):
        path = askdirectory(initialdir=self.session.settings.get('new_model_path'),
                            title="Choose a directory for new model")
        self.set_new_path('new_model_path', path)

    def select_folder_for_test_data(self):
        path = askdirectory(initialdir=self.session.settings.get('test_data_path'),
                            title="Choose directory with test images")
        self.set_new_path('test_data_path', path)

    def load_model(self):
        pass

    def set_new_path(self, gui_var, path):
        if len(path) > 0:
            self.session.settings.set(gui_var, path)
