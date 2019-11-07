import os
import tkinter as tk
from tkinter.filedialog import askdirectory, askopenfilename
from tkinter import ttk

class ConnectionsPage(ttk.Frame):
    name = 'Connections'

    def __init__(self, container, session):
        ttk.Frame.__init__(self, container)
        self.session = session
        self.gui = self.define_gui_elements()
        self.test_show_test()

    def define_gui_elements(self):
        settings = self.session.settings
        gui = dict()
        gui['connected_checkbox'] = ttk.Checkbutton(self, text='FLIMage Connection',
                                                    variable=settings.get_gui_var('pipe_connect_bool'))
        gui['connected_checkbox'].grid(row=0, column=0, sticky='nw', padx=10, pady=3)
        gui['commands_sent_label'] = tk.Label(self, text='Commands Sent',
                                              font=self.session.settings.get('large_font'))
        gui['commands_sent_label'].grid(row=1, column=0, padx=10, pady=10, sticky='nwse')
        gui['commands_received_label'] = tk.Label(self, text='Commands Received',
                                                  font=self.session.settings.get('large_font'))
        gui['commands_received_label'].grid(row=1, column=1, padx=10, pady=10, sticky='nwse')
        gui['commands_sent'] = tk.Text(self, height=30, width=50)
        gui['commands_sent'].config(state='disabled')
        gui['commands_sent'].grid(row=2, column=0, sticky='nw', padx=10, pady=3)
        gui['commands_received'] = tk.Text(self, height=30, width=50)
        gui['commands_received'].config(state='disabled')
        gui['commands_received'].grid(row=2, column=1, sticky='nw', padx=10, pady=3)

        return gui

    def test_show_test(self):
        self.show_text('s', 'command one')
        self.show_text('s', 'command two')
        self.show_text('receive', 'command one')
        self.show_text('Receive', 'command two')

    def show_text(self, send_or_receive, text):
        if send_or_receive[0].lower() == 's':
            self.gui['commands_sent'].config(state='normal')
            self.gui['commands_sent'].insert(1.0, text + '\n')
            self.gui['commands_sent'].config(state='disabled')
        else:
            self.gui['commands_received'].config(state='normal')
            self.gui['commands_received'].insert(1.0, text + '\n')
            self.gui['commands_received'].config(state='disabled')
