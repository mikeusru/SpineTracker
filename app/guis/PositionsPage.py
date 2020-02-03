import tkinter as tk
from tkinter import ttk, simpledialog

import matplotlib
import matplotlib.colorbar as colorbar
import matplotlib.dates
import numpy as np
from matplotlib import patches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from app.io_communication.Event import initialize_events
from app.utilities.DraggableShape import DraggableShape
from app.utilities.helper_functions import fit_fig_to_canvas


class PositionsPage(ttk.Frame):
    name = 'Positions'

    def __init__(self, parent, session):
        ttk.Frame.__init__(self, parent)
        self.gui = dict()
        self.bind("<Visibility>", self.on_visibility)
        self.selected_pos_id = None
        self.draggable_circle = None
        self.draggable_af_rectangle = None
        self.draggable_af_rectangle_zoomed_out = None
        self.settings = {
            'scan_voltage_multiplier': np.array([1, 1]),
            'large_font': None,
            'fig_dpi': 0,
            'fov_x_y': 0
        }
        self.gui_vars = {
            'imaging_zoom': None,
            'reference_zoom': None,
            'imaging_slices': None,
            'reference_slices': None,
            'uncaging_roi_toggle': None,
            'invert_x_position_canvas_axis': None,
            'invert_y_position_canvas_axis': None,
            'af_box_size_um': None,
        }
        self.events = initialize_events([
            'move_to_pos_id',
            'align_position_to_ref',
            'update_position',
            'update_reference_images',
            'remove_position',
            'create_new_position',
            'clear_positions',
            'build_macro_window',
            'align_all_positions_to_refs',
            'image_all_positions',
        ])
        self.shared_figs = None
        self.positions = None

    def build_gui_items(self):
        # GUIs
        self.gui['popup'] = tk.Menu(self, tearoff=0)
        self.gui['popup'].add_command(label="Move To Position",
                                      command=lambda: self.events['move_to_pos_id'](self.selected_pos_id))
        self.gui['popup'].add_command(label="Align to Reference",
                                      command=lambda: self.events['align_position_to_ref'](self.selected_pos_id))
        self.gui['popup'].add_command(label="Update XYZ",
                                      command=lambda: self.events['update_position'](self.selected_pos_id))
        self.gui['popup'].add_command(label="Take New Ref Images",
                                      command=lambda: self.events['update_reference_images'](self.selected_pos_id))
        self.gui['popup'].add_command(label="Delete",
                                      command=lambda: self.events['remove_position'](self.selected_pos_id))
        self.gui['frame_for_buttons'] = ttk.Frame(self)
        self.gui['frame_for_buttons'].grid(column=0, row=0, sticky='nw')
        self.gui['frame_for_zoom'] = ttk.Frame(self)
        self.gui['frame_for_zoom'].grid(column=1, row=3, sticky='ew', padx=10, pady=10)
        self.gui['frame_for_graphics'] = ttk.Frame(self)
        self.gui['frame_for_graphics'].grid(column=1, row=0, sticky='nsew')
        self.gui['button_add_position'] = ttk.Button(self.gui['frame_for_buttons'], text="Add current position",
                                                     command=lambda: self.events['create_new_position'](self))
        self.gui['button_add_position'].grid(row=0, column=0, padx=10, pady=10, sticky='wn')
        self.gui['button_clear_positions'] = ttk.Button(self.gui['frame_for_buttons'], text="Clear All Positions",
                                                        command=lambda: self.events['clear_positions'](self))
        self.gui['button_clear_positions'].grid(row=1, column=0, padx=10,
                                                pady=10, sticky='wn')
        self.gui['button_macro_view'] = ttk.Button(self.gui['frame_for_buttons'], text="Macro View",
                                                   command=lambda: self.events['build_macro_window']())
        self.gui['button_macro_view'].grid(row=2, column=0, padx=10,
                                           pady=10, sticky='wn')
        self.gui['button_align_positions'] = ttk.Button(self.gui['frame_for_buttons'], text="Align All To Reference",
                                                        command=lambda: self.events['align_all_positions_to_refs']())
        self.gui['button_align_positions'].grid(row=3, column=0, padx=10,
                                                pady=10, sticky='wn')
        self.gui['button_cycle_through_positions'] = ttk.Button(self.gui['frame_for_buttons'],
                                                                text="Single Imaging Cycle",
                                                                command=lambda: self.events['image_all_positions']())
        self.gui['button_cycle_through_positions'].grid(row=4, column=0, padx=10,
                                                        pady=10, sticky='wn')

        self.gui['label_imaging_zoom'] = tk.Label(self.gui['frame_for_zoom'], text="Imaging Zoom",
                                                  font=self.settings['large_font'])
        self.gui['label_imaging_zoom'].grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        self.gui['entry_imaging_zoom'] = ttk.Entry(self.gui['frame_for_zoom'],
                                                   textvariable=self.gui_vars['imaging_zoom'])
        self.gui['entry_imaging_zoom'].grid(row=0, column=1, padx=10, pady=10, sticky='nw')
        self.gui['label_ref_zoom'] = tk.Label(self.gui['frame_for_zoom'], text="Reference Zoom",
                                              font=self.settings['large_font'])
        self.gui['label_ref_zoom'].grid(row=0, column=2, sticky='nw', padx=10, pady=10)

        self.gui['entry_ref_zoom'] = ttk.Entry(self.gui['frame_for_zoom'],
                                               textvariable=self.gui_vars['reference_zoom'])
        self.gui['entry_ref_zoom'].grid(row=0, column=3, padx=10, pady=10, sticky='nw')

        self.gui['label_imaging_slices'] = tk.Label(self.gui['frame_for_zoom'], text="Imaging Slices",
                                                    font=self.settings['large_font'])
        self.gui['label_imaging_slices'].grid(row=1, column=0, sticky='nw', padx=10, pady=10)

        self.gui['entry_imaging_slices'] = ttk.Entry(self.gui['frame_for_zoom'],
                                                     textvariable=self.gui_vars['imaging_slices'])
        self.gui['entry_imaging_slices'].grid(row=1, column=1, padx=10, pady=10, sticky='nw')
        self.gui['label_ref_slices'] = tk.Label(self.gui['frame_for_zoom'], text="Reference Slices",
                                                font=self.settings['large_font'])
        self.gui['label_ref_slices'].grid(row=1, column=2, sticky='nw', padx=10, pady=10)

        self.gui['entry_ref_slices'] = ttk.Entry(self.gui['frame_for_zoom'],
                                                 textvariable=self.gui_vars['reference_slices'])
        self.gui['entry_ref_slices'].grid(row=1, column=3, padx=10, pady=10, sticky='nw')

        # Treeview example given at http://knowpapa.com/ttk-treeview/
        self.gui['positions_table_frame'] = ttk.Frame(self.gui['frame_for_graphics'])
        self.gui['positions_table_frame'].grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        self.gui['tree'] = ttk.Treeview(self.gui['positions_table_frame'])
        self.create_positions_table(self.gui['positions_table_frame'])

        # create canvas for previewing reference images
        self.gui['ref_images_fig'] = Figure(figsize=(4, 2), dpi=self.settings['fig_dpi'])
        self.gui['ref_images_fig'].subplots_adjust(left=0, right=1, bottom=0, top=1, wspace=0.02, hspace=0)
        self.gui['popup_canvas_preview_ref_images'] = tk.Menu(self, tearoff=0)
        self.gui['popup_canvas_preview_ref_images'].add_command(label="Change Z Drift Calculation Window",
                                                       command=self.change_z_drift_calc_window)
        self.gui['canvas_preview_ref_images'] = FigureCanvasTkAgg(self.gui['ref_images_fig'],
                                                                  self.gui['frame_for_graphics'])
        self.gui['canvas_preview_ref_images'].get_tk_widget().config(borderwidth=1, background='gray',
                                                                     highlightcolor='gray',
                                                                     highlightbackground='gray')
        self.gui['canvas_preview_ref_images'].draw()
        self.gui['canvas_preview_ref_images'].get_tk_widget().grid(row=1, column=0, padx=10, sticky='nsew')
        self.gui['canvas_preview_ref_images'].get_tk_widget().bind("<Button-3>", self.on_canvas_preview_ref_images_click)

        self.gui['ref_images_axes'] = []
        for i in range(2):
            self.gui['ref_images_axes'].append(self.gui['ref_images_fig'].add_subplot(1, 2, i + 1))
        # relative positions figure
        self.gui['popup_positions_canvas'] = tk.Menu(self, tearoff=0)
        self.gui['popup_positions_canvas'].add_command(label="Invert X Axis",
                                                       command=self.invert_x_axis)
        self.gui['popup_positions_canvas'].add_command(label="Invert Y Axis",
                                                       command=self.invert_y_axis)
        self.gui['f_positions'] = self.shared_figs['f_positions']
        self.gui['canvas_positions'] = FigureCanvasTkAgg(self.gui['f_positions'], self.gui['frame_for_graphics'])
        self.gui['canvas_positions'].draw()
        self.gui['canvas_positions'].get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                                            highlightbackground='gray')
        self.gui['canvas_positions'].get_tk_widget().grid(row=0, column=2, rowspan=2, padx=10, pady=10, sticky='nsew')
        self.gui['canvas_positions'].get_tk_widget().bind("<Button-3>", self.on_canvas_position_click)
        # self.gui['canvas_positions'].mpl_connect("button_press_event", self.on_canvas_position_click)
        self.gui['position_preview_axis'] = self.gui['f_positions'].add_subplot(1, 1, 1)
        self.gui['colorbar_axis'], kw = colorbar.make_axes_gridspec(self.gui['position_preview_axis'])
        self.preview_position_locations()

    def change_z_drift_calc_window(self):
        answer = simpledialog.askfloat("Input", "Enter Box Size for Drift Calculation (µm)", parent=self)
        if answer is float:
            self.gui_vars['af_box_size_um'].set(answer)
            self.select_current_position()

    def on_canvas_preview_ref_images_click(self, event):
        self.gui['popup_canvas_preview_ref_images'].post(event.x_root, event.y_root)

    def on_canvas_position_click(self, event):
        self.gui['popup_positions_canvas'].post(event.x_root, event.y_root)

    def invert_x_axis(self):
        self.gui_vars['invert_x_position_canvas_axis'].set(not self.gui_vars['invert_x_position_canvas_axis'].get())
        self.preview_position_locations()

    def invert_y_axis(self):
        self.gui_vars['invert_y_position_canvas_axis'].set(not self.gui_vars['invert_y_position_canvas_axis'].get())
        self.preview_position_locations()

    def create_positions_table(self, container):
        tree = self.gui['tree']
        tree["columns"] = ("x", "y", "z")
        tree.column("#0", width=160)
        tree.column("x", width=100)
        tree.column("y", width=100)
        tree.column("z", width=100)
        tree.heading("x", text="X")
        tree.heading("y", text="Y")
        tree.heading("z", text="Z")
        tree.bind("<Button-3>", self.on_tree_right_click)
        tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        tree.grid(row=0, column=0, sticky='nsew')
        scroll = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        scroll.grid(row=0, column=1, pady=10, sticky='nsw')
        tree.configure(yscrollcommand=scroll.set)

    def preview_position_locations(self):
        positions = self.positions
        ax = self.gui['position_preview_axis']
        ax.clear()
        self.gui['colorbar_axis'].clear()
        xx = np.array([])
        yy = np.array([])
        zz = np.array([])
        pp = ()
        for pos_id in positions:
            position = positions[pos_id]
            zoom = position['zoom']
            multiplier = self.settings['scan_voltage_multiplier']
            rotation = position['rotation']
            fovxy = position['fov_xy']
            viewsize = fovxy * multiplier / zoom
            w = viewsize[0]
            h = viewsize[1]
            xyz = positions.get_coordinates(pos_id).get_combined()
            xx = np.append(xx, xyz['x'] - w / 2)
            yy = np.append(yy, xyz['y'] - h / 2)
            zz = np.append(zz, xyz['z'])
            polygon = np.array(((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)))
            theta = np.radians(rotation)
            c, s = np.cos(theta), np.sin(theta)
            rotation_matrix = np.array(((c, -s), (s, c)))
            for i in range(0, 4):
                polygon[i, :] = np.dot(rotation_matrix, polygon[i, :])
            polygon[:, 0] += xyz['x']
            polygon[:, 1] += xyz['y']
            pp = pp + (polygon,)

        if len(positions) > 0:
            v_min = zz.min() - 1
            v_max = zz.max() + 1
        else:
            v_min = -100
            v_max = 100

        pos_labels = list(positions.keys())
        c_map = matplotlib.cm.jet
        norm = matplotlib.colors.Normalize(vmin=v_min, vmax=v_max)

        for p, x, y, z, pos in zip(pp, xx, yy, zz, pos_labels):
            ax.add_patch(patches.Polygon(xy=p, fill=True, facecolor=c_map(norm(z))))
            ax.annotate(str(pos), xy=(p[0, :]), xytext=(p[2, :]))

        cb1 = colorbar.ColorbarBase(ax=self.gui['colorbar_axis'], cmap=c_map, norm=norm)
        cb1.set_label('Z (µm)')
        ax.set_ylabel('Y (µm)')
        ax.set_xlabel('X (µm)')
        ax.axis('equal')
        if self.gui_vars['invert_y_position_canvas_axis'].get():
            ax.invert_yaxis()
        if self.gui_vars['invert_x_position_canvas_axis'].get():
            ax.invert_xaxis()
        cb1.ax.yaxis.label.set_size(8)
        ax.xaxis.label.set_size(8)
        ax.yaxis.label.set_size(8)
        ax.relim()
        xlim0, xlim1 = ax.get_xlim()
        ylim0, ylim1 = ax.get_ylim()
        clim0, clim1 = cb1.ax.get_ylim()
        ax.xaxis.set_ticks([int(xlim0), int(xlim1)])
        ax.yaxis.set_ticks([int(ylim0), int(ylim1)])
        cb1.ax.yaxis.set_ticks([int(clim0), int(clim1)])
        ax.autoscale_view()
        self.gui['canvas_positions'].draw_idle()

    def on_visibility(self, event):
        fit_fig_to_canvas(self.gui['f_positions'], self.gui['canvas_positions'],
                          self.settings['fig_dpi'])
        self.redraw_position_table()
        self.gui['canvas_preview_ref_images'].draw_idle()

    def on_tree_right_click(self, event):
        item_text = '1'
        iid = self.gui['tree'].identify_row(event.y)
        if iid:
            # mouse over item
            self.gui['tree'].selection_set(iid)
        if len(self.gui['tree'].selection()) == 0:
            return
        for item in self.gui['tree'].selection():
            item_text = self.gui['tree'].item(item, "text")
        pos_id = int(item_text.split()[1])
        self.selected_pos_id = pos_id
        self.gui['popup'].post(event.x_root, event.y_root)

    def on_tree_select(self, event):
        pos_id = 1
        for item in self.gui['tree'].selection():
            item_text = self.gui['tree'].item(item, "text")
            pos_id = int(item_text.split()[1])
        self.draw_ref_images(pos_id)
        self.preview_position_locations()
        self.select_position_in_graph(pos_id)

    def select_position_in_graph(self, pos_id):
        positions = self.positions
        ax = self.gui['position_preview_axis']
        xyz = positions.get_coordinates(pos_id).get_combined()
        x, y = [xyz[key] for key in ['x', 'y']]
        arrow_props = dict(facecolor='black')
        for annotation in ax.texts:
            if annotation.arrow_patch:
                annotation.remove()
        ax.annotate("", xy=(x, y), xytext=(x - 10, y - 10), arrowprops=arrow_props)
        self.gui['canvas_positions'].draw_idle()

    def redraw_position_table(self):
        for i in self.gui['tree'].get_children():
            self.gui['tree'].delete(i)
        for pos_id in self.positions:
            xyz = self.positions.get_coordinates(pos_id).get_combined()
            x, y, z = [f'{xyz[key]:.1f}' for key in ['x', 'y', 'z']]
            self.gui['tree'].insert("", pos_id, text="Position {0}".format(pos_id),
                                    values=(x, y, z))
        self.preview_position_locations()
        self.gui['canvas_preview_ref_images'].draw_idle()
        self.select_current_position()

    def select_current_position(self, pos_id=0):
        children = self.gui['tree'].get_children('')
        if pos_id == 0:
            n = len(children)
        else:
            n = pos_id
        if n > 0:
            self.gui['tree'].selection_set(children[n - 1])

    def draw_ref_images(self, pos_id):
        refs = [self.positions.get_image(pos_id, zoomed_out=False),
                self.positions.get_image(pos_id, zoomed_out=True)]
        for ax, ref_image in zip(self.gui['ref_images_axes'], refs):
            ax.clear()
            ax.axis('off')
            if ref_image:
                img = ref_image.get_max_projection()
            ax.imshow(img)
        self.draw_roi(pos_id, self.gui['ref_images_axes'][0])
        self.draw_af_boxes(pos_id, self.gui['ref_images_axes'])
        self.gui['canvas_preview_ref_images'].draw_idle()

    def draw_roi(self, pos_id, ax):
        if self.gui_vars['uncaging_roi_toggle']:
            ax_width = abs(np.diff(ax.get_xlim()).item())
            x, y = self.positions.get_roi_x_y(pos_id)
            circle = patches.Circle((x, y), radius=ax_width / 20, fill=False, linewidth=ax_width / 20, edgecolor='r')
            ax.add_patch(circle)
            dc = DraggableShape(self.positions[pos_id], circle)
            dc.connect()
            self.draggable_circle = dc
            self.positions.backup_positions()

    def draw_af_boxes(self, pos_id, ax_list):
        x, y = self.positions.get_roi_x_y(pos_id)
        self.draw_af_box_ref(x, y, pos_id, ax_list[0])
        self.draw_af_box_ref_zoomed_out(x, y, pos_id, ax_list[1])

    def draw_af_box_ref(self, center_x, center_y, pos_id, ax):
        side_um = self.gui_vars['af_box_size_um'].get()
        self.draggable_af_rectangle = self.draw_af_box(side_um, center_x, center_y, pos_id, ax)

    def draw_af_box_ref_zoomed_out(self, center_x, center_y, pos_id, ax):
        fov_x_y = self.settings['fov_x_y'].get()
        zoom = self.positions[pos_id].zoom
        side_um = fov_x_y[0] / zoom
        self.draggable_af_rectangle_zoomed_out = self.draw_af_box(side_um, center_x, center_y, pos_id, ax)

    def draw_af_box(self, side_um, center_x, center_y, pos_id, ax):
        fov_x_y = self.settings['fov_x_y'].get()
        zoom = self.positions[pos_id].zoom
        ax_width = abs(np.diff(ax.get_xlim()).item())
        image_pixels = self.positions[pos_id].get_ref_image_side()
        pixels_per_um = np.array([image_pixels / (fov_x_y[0] / zoom), image_pixels / (fov_x_y[1] / zoom)])
        width_pixels = side_um * pixels_per_um[0] / 2
        height_pixels = side_um * pixels_per_um[1] / 2
        x = center_x - width_pixels / 2
        y = center_y - height_pixels / 2
        rect = patches.Rectangle((x, y), width_pixels, height_pixels, fill=False, linewidth=ax_width / 100,
                                 edgecolor='r')
        ax.add_patch(rect)
        dr = DraggableShape(self.positions[pos_id], rect)
        dr.connect()
        return dr
