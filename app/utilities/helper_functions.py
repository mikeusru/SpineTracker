import os
import matplotlib.pyplot as plt


def fit_fig_to_canvas(fig, canvas, fig_dpi):
    h = canvas.get_tk_widget().winfo_height()
    w = canvas.get_tk_widget().winfo_width()
    fig.set_size_inches(w / fig_dpi, h / fig_dpi)


def remove_keymap_conflicts(new_keys_set):
    for prop in plt.rcParams:
        if prop.startswith('keymap.'):
            keys = plt.rcParams[prop]
            remove_list = set(keys) & new_keys_set
            for key in remove_list:
                keys.remove(key)




