import tkinter as tk
from tkinter import ttk
import matplotlib
import numpy as np
from guis.SettingsPage import SettingsPage
from utilities.DraggableCircle import DraggableCircle
from utilities.helper_functions import fitFigToCanvas
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import patches
import matplotlib.dates
import matplotlib.colorbar as colorbar

matplotlib.use("TkAgg")


class PositionsPage(ttk.Frame):
    name = 'Positions'

    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.popup = tk.Menu(self, tearoff=0)
        self.bind("<Visibility>", self.on_visibility)
        self.controller = controller
        frame_for_buttons = ttk.Frame(self)
        frame_for_buttons.grid(column=0, row=0, sticky='nw')
        frame_for_zoom = ttk.Frame(self)
        frame_for_zoom.grid(column=1, row=3, sticky='ew', padx=10, pady=10)
        frame_for_graphics = ttk.Frame(self)
        frame_for_graphics.grid(column=1, row=0, sticky='nsew')
        button_add_position = ttk.Button(frame_for_buttons, text="Add current position",
                                         command=lambda: controller.add_position(self))
        button_add_position.grid(row=0, column=0, padx=10, pady=10, sticky='wn')
        button_clear_positions = ttk.Button(frame_for_buttons, text="Clear All Positions",
                                            command=lambda: controller.clear_positions(self))
        button_clear_positions.grid(row=1, column=0, padx=10,
                                    pady=10, sticky='wn')
        button_cell_view = ttk.Button(frame_for_buttons, text="Macro View",
                                      command=lambda: controller.show_macro_view_window())
        button_cell_view.grid(row=2, column=0, padx=10,
                              pady=10, sticky='wn')

        label_imaging_zoom = tk.Label(frame_for_zoom, text="Imaging Zoom",
                                      font=self.controller.get_app_param('large_font'))
        label_imaging_zoom.grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        self.imagingZoom = tk.StringVar(self)
        self.imagingZoom.set(self.controller.settings['imagingZoom'])

        # TODO: Clean up the trace function for the stringvar traces
        # def trace_fun(a, b, c, source, name): return self.controller.update_settings(name, source, a, b, c)
        self.imagingZoom.trace('w', lambda a, b, c, source=self.imagingZoom,
                                           name='imagingZoom': self.controller.update_settings(name, source, a, b, c))
        entry_imaging_zoom = ttk.Entry(frame_for_zoom, textvariable=self.imagingZoom)
        entry_imaging_zoom.grid(row=0, column=1, padx=10, pady=10, sticky='nw')
        label_ref_zoom = tk.Label(frame_for_zoom, text="Reference Zoom",
                                  font=self.controller.get_app_param('large_font'))
        label_ref_zoom.grid(row=0, column=2, sticky='nw', padx=10, pady=10)
        self.refZoom = tk.StringVar(self)
        self.refZoom.set(self.controller.settings['referenceZoom'])
        self.refZoom.trace('w', lambda a, b, c, source=self.refZoom,
                                       name='referenceZoom': self.controller.update_settings(name, source, a, b, c))
        entry_ref_zoom = ttk.Entry(frame_for_zoom, textvariable=self.refZoom)
        entry_ref_zoom.grid(row=0, column=3, padx=10, pady=10, sticky='nw')

        label_imaging_slices = tk.Label(frame_for_zoom, text="Imaging Slices",
                                        font=self.controller.get_app_param('large_font'))
        label_imaging_slices.grid(row=1, column=0, sticky='nw', padx=10, pady=10)
        self.imagingSlices = tk.StringVar(self)
        self.imagingSlices.set(self.controller.settings['imagingSlices'])
        self.imagingSlices.trace('w',
                                 lambda a, b, c,
                                        source=self.imagingSlices,
                                        name='imagingSlices':
                                 self.controller.update_settings(name, source, a, b, c))
        entry_imaging_slices = ttk.Entry(frame_for_zoom, textvariable=self.imagingSlices)
        entry_imaging_slices.grid(row=1, column=1, padx=10, pady=10, sticky='nw')
        label_ref_slices = tk.Label(frame_for_zoom, text="Reference Slices",
                                    font=self.controller.get_app_param('large_font'))
        label_ref_slices.grid(row=1, column=2, sticky='nw', padx=10, pady=10)
        self.refSlices = tk.StringVar(self)
        self.refSlices.set(self.controller.settings['referenceSlices'])
        self.refSlices.trace('w',
                             lambda a, b, c,
                                    source=self.refSlices,
                                    name='referenceSlices': self.controller.update_settings(name, source, a, b, c))
        entry_ref_slices = ttk.Entry(frame_for_zoom, textvariable=self.refSlices)
        entry_ref_slices.grid(row=1, column=3, padx=10, pady=10, sticky='nw')

        f_positions = Figure(figsize=(3, 3), dpi=controller.get_app_param('fig_dpi'))
        f_positions.subplots_adjust(left=0, right=1, bottom=0, top=1)
        f_positions.set_tight_layout(True)

        # treeview example given at http://knowpapa.com/ttk-treeview/
        positions_table_frame = ttk.Frame(frame_for_graphics)
        positions_table_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        self.tree = ttk.Treeview(positions_table_frame)
        self.create_positions_table(positions_table_frame)

        # create canvas for previewing reference images
        f1 = Figure(figsize=(4, 2), dpi=controller.get_app_param('fig_dpi'))
        f1.subplots_adjust(left=0, right=1, bottom=0, top=1, wspace=0.02, hspace=0)
        canvas_preview_ref_images = FigureCanvasTkAgg(f1, frame_for_graphics)
        canvas_preview_ref_images.get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                                         highlightbackground='gray')
        canvas_preview_ref_images.show()
        canvas_preview_ref_images.get_tk_widget().grid(row=1, column=0, padx=10, sticky='nsew')
        a1 = []
        self.canvas_previewRefImages = canvas_preview_ref_images
        for i in range(2):
            a1.append(f1.add_subplot(1, 2, i + 1))
        controller.refImgAx = a1
        controller.refImgFig = f1
        # relative positions figure
        f_positions.set_size_inches(4, 4)
        canvas_positions = FigureCanvasTkAgg(f_positions, frame_for_graphics)
        canvas_positions.show()
        canvas_positions.get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                                highlightbackground='gray')
        canvas_positions.get_tk_widget().grid(row=0, column=2, rowspan=2, padx=10, pady=10, sticky='nsew')
        a2 = f_positions.add_subplot(1, 1, 1)
        c_ax, kw = colorbar.make_axes_gridspec(a2)
        self.canvas_positions = canvas_positions
        self.positionPreviewAxis = a2
        self.colorbarAxis = c_ax
        self.preview_position_locations()
        self.draggable_circle = []
        self.selectionArrow = []

    def create_positions_table(self, container):
        tree = self.tree
        tree["columns"] = ("x", "y", "z")
        tree.column("#0", width=300)
        tree.column("x", width=30)
        tree.column("y", width=30)
        tree.column("z", width=50)
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
        positions = self.controller.positions
        ax = self.positionPreviewAxis
        c_ax = self.colorbarAxis
        w = 8
        h = 8
        ax.clear()
        c_ax.clear()
        xx = np.array([])
        yy = np.array([])
        zz = np.array([])
        for pos_id in positions:
            xx = np.append(xx, positions[pos_id]['x'])
            yy = np.append(yy, positions[pos_id]['y'])
            zz = np.append(zz, positions[pos_id]['z'])

        if len(positions) > 0:
            vmin = zz.min() - 1
            vmax = zz.max() + 1
        else:
            vmin = -100
            vmax = 100

        pos_labels = list(positions.keys())
        cmap = matplotlib.cm.jet
        norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
        for x, y, z, p in zip(xx, yy, zz, pos_labels):
            ax.add_patch(patches.Rectangle(xy=(x, y), width=w, height=h,
                                           facecolor=cmap(norm(z))))
            ax.annotate(str(p), xy=(x, y), xytext=(x + w, y + h))
        cb1 = colorbar.ColorbarBase(ax=c_ax, cmap=cmap, norm=norm)
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
        self.canvas_positions.draw_idle()

    def on_visibility(self, event):
        fitFigToCanvas(self.controller.f_positions, self.canvas_positions, self.controller.get_app_param('fig_dpi'))
        self.redraw_position_table()
        self.canvas_previewRefImages.draw_idle()

    def on_tree_right_click(self, event):
        item_text = '1'
        iid = self.tree.identify_row(event.y)
        if iid:
            # mouse over item
            self.tree.selection_set(iid)
        if len(self.tree.selection()) == 0:
            return
        for item in self.tree.selection():
            item_text = self.tree.item(item, "text")
        pos_id = int(item_text.split()[1])
        self.popup.add_command(label="Update XYZ", command=lambda: self.controller.update_position(pos_id))
        self.popup.add_command(label="Delete", command=lambda: self.controller.delete_positions(pos_id))
        self.popup.post(event.x_root, event.y_root)

    def on_tree_select(self, event):
        pos_id = 1
        for item in self.tree.selection():
            item_text = self.tree.item(item, "text")
            pos_id = int(item_text.split()[1])
        self.draw_ref_images(pos_id)
        self.select_position_in_graph(pos_id)

    def select_position_in_graph(self, pos_id):
        positions = self.controller.positions
        ax = self.positionPreviewAxis
        x = positions[pos_id]['x']
        y = positions[pos_id]['y']
        arrowprops = dict(facecolor='black')
        arrow = ax.annotate("", xy=(x, y), xytext=(x - 10, y - 10), arrowprops=arrowprops)
        try:
            self.selectionArrow.remove()
        except:
            pass
        self.selectionArrow = arrow
        self.canvas_positions.draw_idle()

    def redraw_position_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for pos_id in self.controller.positions:
            x = self.controller.positions[pos_id]['x']
            y = self.controller.positions[pos_id]['y']
            z = self.controller.positions[pos_id]['z']
            self.tree.insert("", pos_id, text="Position {0}".format(pos_id),
                             values=(x, y, z))
        self.preview_position_locations()
        self.canvas_previewRefImages.draw_idle()

    def draw_ref_images(self, pos_id):
        refs = [self.controller.positions[pos_id]['refImg'], self.controller.positions[pos_id]['refImgZoomout']]
        for ax, r in zip(self.controller.refImgAx, refs):
            ax.clear()
            ax.axis('off')
            ax.imshow(r)
        self.draw_roi(pos_id, self.controller.refImgAx[0])
        self.canvas_previewRefImages.draw_idle()

    def draw_roi(self, pos_id, ax):
        if self.controller.frames[SettingsPage].uncaging_roi_toggle:
            ax_width = abs(np.diff(ax.get_xlim()).item())
            x, y = self.controller.positions[pos_id]['roi_position']
            circ = patches.Circle((x, y), radius=ax_width / 20, fill=False, linewidth=ax_width / 20, edgecolor='r')
            ax.add_patch(circ)
            dc = DraggableCircle(self, self.controller.positions[pos_id], circ)
            dc.connect()
            self.draggable_circle = dc
