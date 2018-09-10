import tkinter as tk
from tkinter import ttk
import matplotlib
import numpy as np
from utilities.DraggableCircle import DraggableCircle
from utilities.helper_functions import fit_fig_to_canvas
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import patches
import matplotlib.dates
import matplotlib.colorbar as colorbar

matplotlib.use("TkAgg")


class PositionsPage(ttk.Frame):
    name = 'Positions'

    def __init__(self, parent, session):
        ttk.Frame.__init__(self, parent)
        self.gui = dict()
        self.bind("<Visibility>", self.on_visibility)
        self.session = session

        self.selected_pos_id = None
        self.draggable_circle = None
        settings = self.session.settings
        # GUIs
        self.gui['popup'] = tk.Menu(self, tearoff=0)
        self.gui['popup'].add_command(label="Move To Position",
                                      command=lambda: self.session.move_to_pos_id(pos_id=self.selected_pos_id))
        self.gui['popup'].add_command(label="Update XYZ",
                                      command=lambda: self.session.update_position(self.selected_pos_id))
        self.gui['popup'].add_command(label="Delete",
                                      command=lambda: self.session.remove_position(self.selected_pos_id))

        self.gui['frame_for_buttons'] = ttk.Frame(self)
        self.gui['frame_for_buttons'].grid(column=0, row=0, sticky='nw')
        self.gui['frame_for_zoom'] = ttk.Frame(self)
        self.gui['frame_for_zoom'].grid(column=1, row=3, sticky='ew', padx=10, pady=10)
        self.gui['frame_for_graphics'] = ttk.Frame(self)
        self.gui['frame_for_graphics'].grid(column=1, row=0, sticky='nsew')
        self.gui['button_add_position'] = ttk.Button(self.gui['frame_for_buttons'], text="Add current position",
                                                     command=lambda: session.create_new_position(self))
        self.gui['button_add_position'].grid(row=0, column=0, padx=10, pady=10, sticky='wn')
        self.gui['button_clear_positions'] = ttk.Button(self.gui['frame_for_buttons'], text="Clear All Positions",
                                                        command=lambda: session.clear_positions(self))
        self.gui['button_clear_positions'].grid(row=1, column=0, padx=10,
                                                pady=10, sticky='wn')
        self.gui['button_macro_view'] = ttk.Button(self.gui['frame_for_buttons'], text="Macro View",
                                                   command=lambda: session.gui.build_macro_window())
        self.gui['button_macro_view'].grid(row=2, column=0, padx=10,
                                           pady=10, sticky='wn')
        self.gui['button_align_positions'] = ttk.Button(self.gui['frame_for_buttons'], text="Align All To Reference",
                                                        command=lambda: session.align_all_positions_to_refs())
        self.gui['button_align_positions'].grid(row=3, column=0, padx=10,
                                                pady=10, sticky='wn')

        self.gui['label_imaging_zoom'] = tk.Label(self.gui['frame_for_zoom'], text="Imaging Zoom",
                                                  font=settings.get('large_font'))
        self.gui['label_imaging_zoom'].grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        self.gui['entry_imaging_zoom'] = ttk.Entry(self.gui['frame_for_zoom'],
                                                   textvariable=settings.get_gui_var('imaging_zoom'))
        self.gui['entry_imaging_zoom'].grid(row=0, column=1, padx=10, pady=10, sticky='nw')
        self.gui['label_ref_zoom'] = tk.Label(self.gui['frame_for_zoom'], text="Reference Zoom",
                                              font=settings.get('large_font'))
        self.gui['label_ref_zoom'].grid(row=0, column=2, sticky='nw', padx=10, pady=10)

        self.gui['entry_ref_zoom'] = ttk.Entry(self.gui['frame_for_zoom'],
                                               textvariable=settings.get_gui_var('reference_zoom'))
        self.gui['entry_ref_zoom'].grid(row=0, column=3, padx=10, pady=10, sticky='nw')

        self.gui['label_imaging_slices'] = tk.Label(self.gui['frame_for_zoom'], text="Imaging Slices",
                                                    font=settings.get('large_font'))
        self.gui['label_imaging_slices'].grid(row=1, column=0, sticky='nw', padx=10, pady=10)

        self.gui['entry_imaging_slices'] = ttk.Entry(self.gui['frame_for_zoom'],
                                                     textvariable=settings.get_gui_var('imaging_slices'))
        self.gui['entry_imaging_slices'].grid(row=1, column=1, padx=10, pady=10, sticky='nw')
        self.gui['label_ref_slices'] = tk.Label(self.gui['frame_for_zoom'], text="Reference Slices",
                                                font=settings.get('large_font'))
        self.gui['label_ref_slices'].grid(row=1, column=2, sticky='nw', padx=10, pady=10)

        self.gui['entry_ref_slices'] = ttk.Entry(self.gui['frame_for_zoom'],
                                                 textvariable=settings.get_gui_var('reference_slices'))
        self.gui['entry_ref_slices'].grid(row=1, column=3, padx=10, pady=10, sticky='nw')

        # Treeview example given at http://knowpapa.com/ttk-treeview/
        self.gui['positions_table_frame'] = ttk.Frame(self.gui['frame_for_graphics'])
        self.gui['positions_table_frame'].grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        self.gui['tree'] = ttk.Treeview(self.gui['positions_table_frame'])
        self.create_positions_table(self.gui['positions_table_frame'])

        # create canvas for previewing reference images
        self.gui['ref_images_fig'] = Figure(figsize=(4, 2), dpi=session.settings.get('fig_dpi'))
        self.gui['ref_images_fig'].subplots_adjust(left=0, right=1, bottom=0, top=1, wspace=0.02, hspace=0)
        self.gui['canvas_preview_ref_images'] = FigureCanvasTkAgg(self.gui['ref_images_fig'],
                                                                  self.gui['frame_for_graphics'])
        self.gui['canvas_preview_ref_images'].get_tk_widget().config(borderwidth=1, background='gray',
                                                                     highlightcolor='gray',
                                                                     highlightbackground='gray')
        self.gui['canvas_preview_ref_images'].draw()
        self.gui['canvas_preview_ref_images'].get_tk_widget().grid(row=1, column=0, padx=10, sticky='nsew')
        self.gui['ref_images_axes'] = []
        for i in range(2):
            self.gui['ref_images_axes'].append(self.gui['ref_images_fig'].add_subplot(1, 2, i + 1))
        # relative positions figure
        self.gui['f_positions'] = self.session.gui.shared_figs['f_positions']
        self.gui['canvas_positions'] = FigureCanvasTkAgg(self.gui['f_positions'], self.gui['frame_for_graphics'])
        self.gui['canvas_positions'].draw()
        self.gui['canvas_positions'].get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                                            highlightbackground='gray')
        self.gui['canvas_positions'].get_tk_widget().grid(row=0, column=2, rowspan=2, padx=10, pady=10, sticky='nsew')
        self.gui['position_preview_axis'] = self.gui['f_positions'].add_subplot(1, 1, 1)
        self.gui['colorbar_axis'], kw = colorbar.make_axes_gridspec(self.gui['position_preview_axis'])
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
        positions = self.session.positions
        ax = self.gui['position_preview_axis']
        w = 8
        h = 8
        ax.clear()
        self.gui['colorbar_axis'].clear()
        xx = np.array([])
        yy = np.array([])
        zz = np.array([])
        for pos_id in positions:
            xyz = self.session.positions.get_coordinates(pos_id).get_combined(self.session)
            xx = np.append(xx, xyz['x'])
            yy = np.append(yy, xyz['y'])
            zz = np.append(zz, xyz['z'])

        if len(positions) > 0:
            v_min = zz.min() - 1
            v_max = zz.max() + 1
        else:
            v_min = -100
            v_max = 100

        pos_labels = list(positions.keys())
        c_map = matplotlib.cm.jet
        norm = matplotlib.colors.Normalize(vmin=v_min, vmax=v_max)
        for x, y, z, p in zip(xx, yy, zz, pos_labels):
            ax.add_patch(patches.Rectangle(xy=(x, y), width=w, height=h,
                                           facecolor=c_map(norm(z))))
            ax.annotate(str(p), xy=(x, y), xytext=(x + w, y + h))
        cb1 = colorbar.ColorbarBase(ax=self.gui['colorbar_axis'], cmap=c_map, norm=norm)
        cb1.set_label('Z (µm)')
        ax.set_ylabel('Y (µm)')
        ax.set_xlabel('X (µm)')
        ax.axis('equal')
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
                          self.session.settings.get('fig_dpi'))
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
        self.select_position_in_graph(pos_id)

    def select_position_in_graph(self, pos_id):
        positions = self.session.positions
        ax = self.gui['position_preview_axis']
        xyz = positions.get_coordinates(pos_id).get_combined(self.session)
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
        for pos_id in self.session.positions:
            xyz = self.session.positions.get_coordinates(pos_id).get_combined(self.session)
            x, y, z = [f'{xyz[key]:.1f}' for key in ['x', 'y', 'z']]
            self.gui['tree'].insert("", pos_id, text="Position {0}".format(pos_id),
                                    values=(x, y, z))
        self.preview_position_locations()
        self.gui['canvas_preview_ref_images'].draw_idle()
        self.gui['tree'].after(100, self.select_current_position)

    def select_current_position(self):
        children = self.gui['tree'].get_children('')
        for child in children:
            item = child
        if len(children) > 0:
            self.gui['tree'].selection_set(item)

    def draw_ref_images(self, pos_id):
        refs = [self.session.positions.get_image(pos_id, zoomed_out=False),
                self.session.positions.get_image(pos_id, zoomed_out=True)]
        for ax, ref_image in zip(self.gui['ref_images_axes'], refs):
            ax.clear()
            ax.axis('off')
            ax.imshow(ref_image.get_max_projection())
        self.draw_roi(pos_id, self.gui['ref_images_axes'][0])
        self.gui['canvas_preview_ref_images'].draw_idle()

    def draw_roi(self, pos_id, ax):
        if self.session.settings.get('uncaging_roi_toggle'):
            ax_width = abs(np.diff(ax.get_xlim()).item())
            x, y = self.session.positions.get_roi_x_y(pos_id)
            circle = patches.Circle((x, y), radius=ax_width / 20, fill=False, linewidth=ax_width / 20, edgecolor='r')
            ax.add_patch(circle)
            dc = DraggableCircle(self.session, self.session.positions[pos_id], circle)
            dc.connect()
            self.draggable_circle = dc
