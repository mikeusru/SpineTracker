import tkinter as tk
from tkinter import ttk

from io_communication.Event import initialize_events


class ConnectionsPage(ttk.Frame):
    name = 'Connections'

    def __init__(self, container, session):
        ttk.Frame.__init__(self, container)
        self.gui = None
        self.settings = {
            'large_font': None,
        }
        self.gui_vars = {
            'pipe_connect_bool': None,
        }
        self.events = initialize_events([])

    def build_gui_items(self):
        gui = dict()
        gui['connected_checkbox'] = ttk.Checkbutton(self, text='FLIMage Connection',
                                                    variable=self.gui_vars['pipe_connect_bool'])
        gui['connected_checkbox'].grid(row=0, column=0, sticky='nw', padx=10, pady=3)
        gui['commands_sent_label'] = tk.Label(self, text='Commands Sent',
                                              font=self.settings['large_font'])
        gui['commands_sent_label'].grid(row=1, column=0, padx=10, pady=10, sticky='nwse')
        gui['commands_received_label'] = tk.Label(self, text='Commands Received',
                                                  font=self.settings['large_font'])
        gui['commands_received_label'].grid(row=1, column=1, padx=10, pady=10, sticky='nwse')
        gui['commands_sent'] = tk.Text(self, height=30, width=50)
        gui['commands_sent'].config(state='disabled')
        gui['commands_sent'].grid(row=2, column=0, sticky='nw', padx=10, pady=3)
        gui['commands_received'] = tk.Text(self, height=30, width=50)
        gui['commands_received'].config(state='disabled')
        gui['commands_received'].grid(row=2, column=1, sticky='nw', padx=10, pady=3)

        return gui

    def show_text(self, send_or_receive, text):
        if send_or_receive[0].lower() == 's':
            self.gui['commands_sent'].config(state='normal')
            self.gui['commands_sent'].insert(1.0, text + '\n')
            self.gui['commands_sent'].config(state='disabled')
        else:
            self.gui['commands_received'].config(state='normal')
            self.gui['commands_received'].insert(1.0, text + '\n')
            self.gui['commands_received'].config(state='disabled')
