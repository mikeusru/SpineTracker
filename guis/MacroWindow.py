import tkinter as tk
from tkinter import ttk
import matplotlib
import numpy as np
from PIL import ImageTk, ImageMath
from skimage import transform

from utilities.math_helpers import round_math

matplotlib.use("TkAgg")


class MacroWindow(tk.Toplevel):
    def __init__(self, session, *args, **kwargs):
        tk.Toplevel.__init__(self, *args, **kwargs)
        self.session = session
        self.title("Macro View")
        self.geometry(newGeometry='700x800+200+200')
        self.gui = self.define_gui_elements()
        self.settings = self.session.settings
        self.slice_index = 0
        self.data = dict()
        self.image = None

    def define_gui_elements(self):
        settings = self.session.settings
        gui = dict()
        gui['frame_canvas'] = ttk.Frame(self)
        gui['scrollingCanvas'] = ScrolledCanvas(gui['frame_canvas'], self, self.session)
        gui['scale_z'] = tk.Scale(gui['frame_canvas'], orient=tk.VERTICAL)
        gui['frame_buttons'] = ttk.Frame(self)
        gui['button_load_test_macro_image'] = ttk.Button(gui['frame_buttons'], text="Load Test Macro Image",
                                                         command=lambda: self.load_macro_image())
        gui['label_macro_zoom'] = tk.Label(gui['frame_buttons'], text="Macro Zoom",
                                           font=self.session.settings.get('large_font'))
        gui['entry_macro_zoom'] = ttk.Entry(gui['frame_buttons'],
                                            textvariable=settings.get_gui_var('macro_zoom'),
                                            width=3)
        gui['scale_zoom'] = tk.Scale(self, orient=tk.HORIZONTAL)
        gui['label_z_slices'] = tk.Label(gui['frame_buttons'], text="Number of Z Slices",
                                         font=self.session.settings.get('large_font'))
        gui['entry_z_slices'] = ttk.Entry(gui['frame_buttons'],
                                          textvariable=settings.get_gui_var('macro_z_slices'),
                                          width=4)
        gui['button_load_macro_image'] = ttk.Button(gui['frame_buttons'], text="Grab Macro Image",
                                                    command=lambda: self.load_macro_image())

        # Arrange GUI elements
        gui['frame_canvas'].grid(row=0, column=0, sticky='nsew')
        gui['scale_z'].grid(row=0, column=2, sticky='ns')
        gui['frame_buttons'].grid(row=2, column=0, sticky='nsew')
        gui['button_load_test_macro_image'].grid(row=2, column=0, padx=10, pady=10, sticky='nw')
        gui['label_macro_zoom'].grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        gui['entry_macro_zoom'].grid(row=0, column=1, padx=10, pady=10, sticky='nw')
        gui['scale_zoom'].grid(row=1, column=0, sticky='ew')
        gui['scale_zoom'].config(command=self.change_image_size, from_=.1, to=5, resolution=.1)
        gui['scale_zoom'].set(2)

        gui['label_z_slices'].grid(row=1, column=0, padx=10, pady=10, sticky='nw')
        gui['entry_z_slices'].grid(row=1, column=1, padx=10, pady=10, sticky='nw')

        gui['button_load_macro_image'].grid(row=2, column=1, padx=10, pady=10, sticky='nw')
        return gui

    def change_image_size(self, event):
        if self.image:
            self.gui['scrollingCanvas'].set_image()

    def load_macro_image(self):
        self.session.collect_new_macro_image()
        # TODO: Loading this image doesn't always work. Figure out why... Sometimes, it loads the old image.
        # TODO: open this image automatically when macro window is launched
        self.session.communication.get_motor_position()
        xyz = self.session.state.current_coordinates.get_combined()
        self.session.state.center_coordinates.set_motor(xyz['x'], xyz['y'], xyz['z'])
        self.image = self.session.state.macro_image.pil_image
        self.multi_slice_viewer()

    def multi_slice_viewer(self):
        self.gui['scale_z'].config(command=self.scale_callback, from_=0, to=self.image.n_frames - 1)
        self.slice_index = self.image.n_frames // 2
        self.gui['scale_z'].set(self.slice_index)
        self.gui['scrollingCanvas'].set_image()

    def scale_callback(self, event):
        self.slice_index = self.gui['scale_z'].get()
        self.gui['scrollingCanvas'].set_image()

    def add_position_on_image_click(self, x, y, z):
        # translate to normal coordinates
        fov_x, fov_y = np.array([self.session.settings.get('fov_x'), self.session.settings.get('fov_y')]) / float(
            self.session.settings.get('macro_zoom'))
        # xy currently originate from top left of image.
        # translate them to coordinate plane directionality.
        # also, make them originate from center
        xyz_center = self.session.state.center_coordinates.get_motor()
        xyz_clicked = {'x': x, 'y': y, 'z': z}
        x = x - .5
        y = -y + .5
        # translate coordinates to µm
        x = x * fov_x + xyz_center['x']
        y = y * fov_y + xyz_center['y']
        z = z + xyz_center['z'] - self.image.n_frames / 2
        # add coordinates to position table
        print('x, y, z = {0}, {1}, {2}'.format(x, y, z))
        self.session.state.current_coordinates.set_scan_voltages_x_y(0, 0)
        self.session.state.current_coordinates.set_motor(x, y, z)
        self.get_ref_images_from_macro(xyz_clicked)
        self.session.create_new_position(take_new_refs=False)

    def get_ref_images_from_macro(self, xyz_clicked):
        image_ref = self.get_ref_image_from_macro(xyz_clicked)
        image_ref_zoomed_out = self.get_zoomed_out_ref_image_from_macro(xyz_clicked)
        self.session.state.ref_image.set_stack(image_ref)
        self.session.state.ref_image_zoomed_out.set_stack(image_ref_zoomed_out)

    def get_ref_image_from_macro(self, xyz_clicked):
        zoom = float(self.session.settings.get('imaging_zoom'))
        slice_count = self.session.settings.get('imaging_slices')
        slice_index = self.get_slice_index(slice_count)
        pixel_index_x_y = self.identify_image_pixel_indices(xyz_clicked, zoom)
        image_ref = self.build_reference_image(slice_index, pixel_index_x_y)
        return image_ref

    def get_zoomed_out_ref_image_from_macro(self, xyz_clicked):
        zoom = float(self.session.settings.get('reference_zoom'))
        slice_count = int(self.session.settings.get('reference_slices'))
        slice_index = self.get_slice_index(slice_count)
        pixel_index_x_y = self.identify_image_pixel_indices(xyz_clicked, zoom)
        image_ref_zoomed_out = self.build_reference_image(slice_index, pixel_index_x_y)
        return image_ref_zoomed_out

    def get_slice_index(self, slice_count):
        current_slice_index = self.slice_index
        slice_index = np.array(range(int(max(round_math(current_slice_index - slice_count / 2), 0)),
                                     int(min(round_math(current_slice_index + slice_count / 2),
                                             self.image.n_frames - 1))))
        return slice_index

    def identify_image_pixel_indices(self, xyz_clicked, zoom):
        macro_zoom = float(self.session.settings.get('macro_zoom'))
        height, width = self.image.size
        box_x = width / zoom * macro_zoom
        box_y = height / zoom * macro_zoom
        x_clicked_pixel = width * xyz_clicked['x']
        y_clicked_pixel = height * xyz_clicked['y']
        x_index = np.s_[int(max(round_math(x_clicked_pixel - box_x / 2), 0)): int(
            round_math(x_clicked_pixel + box_x / 2))]
        y_index = np.s_[int(max(round_math(y_clicked_pixel - box_y / 2), 0)): int(
            round_math(y_clicked_pixel + box_y / 2))]
        return x_index, y_index

    def build_reference_image(self, slices_index, pixel_index_x_y):
        x_ind, y_ind = pixel_index_x_y
        resolution_x = float(self.session.settings.get('normal_resolution_x'))
        resolution_y = float(self.session.settings.get('normal_resolution_y'))
        image_stack = self.session.state.macro_image.image_stack  # use original image
        image_stack_sliced = image_stack[slices_index, y_ind, x_ind]
        image_stack_resized = self.resize_image_stack(image_stack_sliced, resolution_x, resolution_y)
        return image_stack_resized

    def resize_image_stack(self, image_stack, resolution_x, resolution_y):
        image_stack_resized = [transform.resize(image, (resolution_x, resolution_y)) for image in image_stack]
        image_stack_resized = np.array(image_stack_resized)
        return image_stack_resized


class ScrolledCanvas(tk.Frame):
    def __init__(self, parent, master, session):
        tk.Frame.__init__(self, parent)
        self.grid(row=0, column=0)
        self.parent = parent
        self.session = session
        self.master = master
        self.gui = {'canvas': tk.Canvas(self, relief=tk.SUNKEN)}
        self.gui['canvas'].bind('<Button-3>', func=self.canvas_right_click)
        self.gui['canvas'].config(width=600, height=600)
        self.gui['canvas'].config(highlightthickness=0)

        self.gui['scrollbar_v'] = tk.Scrollbar(self, orient=tk.VERTICAL)

        self.gui['scrollbar_h'] = tk.Scrollbar(self, orient=tk.HORIZONTAL)

        self.gui['scrollbar_v'].config(command=self.gui['canvas'].yview)
        self.gui['scrollbar_h'].config(command=self.gui['canvas'].xview)

        self.gui['canvas'].config(yscrollcommand=self.gui['scrollbar_v'].set)
        self.gui['canvas'].config(xscrollcommand=self.gui['scrollbar_h'].set)

        self.gui['scrollbar_v'].grid(row=0, column=1, sticky='ns')
        self.gui['scrollbar_h'].grid(row=1, column=0, sticky='ew')

        self.gui['canvas'].grid(row=0, column=0, sticky='nsew')
        self.gui['popup'] = None  # otherwise values are added every time
        self.image_show = None

    def canvas_right_click(self, event):
        # Create popup menu
        w, h = self.master.image.size
        canvas = event.widget
        x = canvas.canvasx(event.x) / (w * self.master.gui['scale_zoom'].get())
        y = canvas.canvasy(event.y) / (h * self.master.gui['scale_zoom'].get())
        if x > 1 or y > 1:
            return
        z = self.master.slice_index
        self.gui['popup'] = tk.Menu(self, tearoff=0)
        self.gui['popup'].add_command(label='Add Position',
                                      command=lambda: self.master.add_position_on_image_click(x, y, z))
        # display the popup menu
        self.gui['popup'].post(event.x_root, event.y_root)

    def set_image(self):
        im = self.master.image
        frame = self.master.slice_index
        zoom = self.master.gui['scale_zoom'].get()
        width, height = im.size
        width_r = round(width * zoom)
        height_r = round(height * zoom)
        im.seek(frame)  # move to appropriate frame
        # rescale to uint8 for accurate display in TkInter
        im_max = np.array(im).max()
        im = ImageMath.eval("float(a)", a=im)
        im = ImageMath.eval("convert(a/a_m * 255, 'L')", a=im, a_m=im_max)
        im_r = im.resize((width_r, height_r))
        self.gui['canvas'].config(scrollregion=(0, 0, width_r, height_r))
        self.image_show = ImageTk.PhotoImage(master=self.gui['canvas'], image=im_r)
        self.gui['imgtag'] = self.gui['canvas'].create_image(0, 0, anchor="nw", image=self.image_show)
