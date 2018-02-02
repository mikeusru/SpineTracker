import os
import matplotlib.pyplot as plt


def fit_fig_to_canvas(fig, canv, fig_dpi):
    # TODO: add fig_dpi to calls for this function, or put it in a Class with DPI info
    h = canv.get_tk_widget().winfo_height()
    w = canv.get_tk_widget().winfo_width()
    fig.set_size_inches(w / fig_dpi, h / fig_dpi)


def remove_keymap_conflicts(new_keys_set):
    for prop in plt.rcParams:
        if prop.startswith('keymap.'):
            keys = plt.rcParams[prop]
            remove_list = set(keys) & new_keys_set
            for key in remove_list:
                keys.remove(key)


def initialize_init_directory(initDirectory):
    directory = os.path.dirname(initDirectory)
    try:
        os.stat(directory)
    except:
        os.mkdir(directory)
