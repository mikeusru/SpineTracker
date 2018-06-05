import tkinter as tk
from tkinter import ttk
import matplotlib
import numpy as np
from PIL import Image, ImageTk, ImageMath, ImageOps
from skimage import transform

from guis.PositionsPage import PositionsPage
from utilities.math_helpers import round_math, histogram_equalize, contrast_stretch

matplotlib.use("TkAgg")


class MacroWindow(tk.Toplevel):
    def __init__(self, controller, *args, **kwargs):
        tk.Toplevel.__init__(self, *args, **kwargs)  # initialize regular Tk stuff

        self.controller = controller

        # set properties for main window
        self.title("Macro View")
        self.geometry(newGeometry='700x800+200+200')

        settings = self.controller.settings

        # Define GUI Elements
        self.gui = dict(frame_canvas=ttk.Frame(self))
        self.gui['scrollingCanvas'] = ScrolledCanvas(self.gui['frame_canvas'], self, self.controller)
        self.gui['scale_z'] = tk.Scale(self.gui['frame_canvas'], orient=tk.VERTICAL)
        self.gui['frame_buttons'] = ttk.Frame(self)
        self.gui['button_load_test_macro_image'] = ttk.Button(self.gui['frame_buttons'], text="Load Test Macro Image",
                                                              command=lambda: self.load_macro_image())
        self.gui['label_macro_zoom'] = tk.Label(self.gui['frame_buttons'], text="Macro Zoom",
                                                font=controller.settings.get('large_font'))
        self.gui['entry_macro_zoom'] = ttk.Entry(self.gui['frame_buttons'],
                                                 textvariable=settings.get_gui_var('macro_zoom'),
                                                 width=3)
        self.gui['scale_zoom'] = tk.Scale(self, orient=tk.HORIZONTAL)
        self.gui['label_z_slices'] = tk.Label(self.gui['frame_buttons'], text="Number of Z Slices",
                                              font=controller.settings.get('large_font'))
        self.gui['entry_z_slices'] = ttk.Entry(self.gui['frame_buttons'],
                                               textvariable=settings.get_gui_var('macro_z_slices'),
                                               width=4)
        self.gui['button_load_macro_image'] = ttk.Button(self.gui['frame_buttons'], text="Grab Macro Image",
                                                         command=lambda: self.load_macro_image())

        # Arrange GUI elements
        self.gui['frame_canvas'].grid(row=0, column=0, sticky='nsew')
        self.gui['scale_z'].grid(row=0, column=2, sticky='ns')
        self.gui['frame_buttons'].grid(row=2, column=0, sticky='nsew')
        self.gui['button_load_test_macro_image'].grid(row=2, column=0, padx=10, pady=10, sticky='nw')
        self.gui['label_macro_zoom'].grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        self.gui['entry_macro_zoom'].grid(row=0, column=1, padx=10, pady=10, sticky='nw')
        self.gui['scale_zoom'].grid(row=1, column=0, sticky='ew')
        self.gui['scale_zoom'].config(command=self.change_image_size, from_=.1, to=5, resolution=.1)
        self.gui['scale_zoom'].set(2)

        self.gui['label_z_slices'].grid(row=1, column=0, padx=10, pady=10, sticky='nw')
        self.gui['entry_z_slices'].grid(row=1, column=1, padx=10, pady=10, sticky='nw')

        self.gui['button_load_macro_image'].grid(row=2, column=1, padx=10, pady=10, sticky='nw')

        # Define other settings
        self.slice_index = 0
        self.data = dict()
        self.image = None

    def change_image_size(self, event):
        if self.image:
            self.gui['scrollingCanvas'].set_image()

    def load_macro_image(self):
        if self.controller.settings.get('simulation'):
            self.image = Image.open("../test/macroImage.tif")
            self.controller.settings.set('center_xyz', np.array((0, 0, 0)))
        else:
            # set macro zoom and resolution
            self.controller.set_macro_imaging_conditions()
            # grab stack
            self.controller.grab_stack()
            # TODO: Loading this image doesn't always work. Figure out why... Sometimes, it loads the old image.
            self.controller.load_acquired_image(update_figure=False, get_macro=True)
            # make sure image is in correct range
            image_stack = np.array([contrast_stretch(img) for img in self.controller.settings.get('macro_image')])
            image_stack = image_stack / np.max(image_stack) * 255
            # since PIL doesn't support creating multiframe images, save the image and load it as a workaround for now.
            imlist = []
            for im in image_stack:
                imlist.append(Image.fromarray(im.astype(np.uint8)))
            imlist[0].save("../temp/macroImage.tif", compression="tiff_deflate", save_all=True,
                           append_images=imlist[1:])
            self.image = Image.open("../temp/macroImage.tif")
            # TODO: open this image automatically when macro window is launched
            # get the motor coordinates
            self.controller.get_current_position()
            x, y, z = self.controller.settings.get('current_coordinates')
            self.controller.settings.set('center_xyz', np.array((x, y, z), dtype=np.float))

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
        fov_x, fov_y = np.array(self.controller.settings['fov_x_y']) / float(self.controller.settings.get('macro_zoom'))
        # xy currently originate from top left of image.
        # translate them to coordinate plane directionality.
        # also, make them originate from center
        x_center, y_center, z_center = self.controller.settings.get('center_xyz')
        xyz_clicked = {'x': x, 'y': y, 'z': z}
        x = x - .5
        y = -y + .5
        # translate coordinates to µm
        x = x * fov_x + x_center
        y = y * fov_y + y_center
        z = z + z_center - self.image.n_frames / 2
        # add coordinates to position table
        print('x, y, z = {0}, {1}, {2}'.format(x, y, z))
        xyz = {'x': x, 'y': y, 'z': z}
        self.get_ref_images_from_macro(xyz_clicked)
        self.controller.add_position(self.controller.frames[PositionsPage], xyz=xyz, ref_images=self.data['refImages'])

    def get_ref_images_from_macro(self, xyz_clicked):
        macro_zoom = float(self.controller.settings.get('macro_zoom'))
        imaging_zoom = float(self.controller.settings.get('imaging_zoom'))
        ref_zoom = float(self.controller.settings.get('reference_zoom'))
        imaging_slices = int(self.controller.settings.get('imaging_slices'))
        ref_slices = int(self.controller.settings.get('reference_slices'))
        resolution_x = float(self.controller.settings.get('normal_resolution_x'))
        resolution_y = float(self.controller.settings.get('normal_resolution_y'))


        frame = self.slice_index
        imaging_slices_ind = np.array(range(int(max(round_math(frame - imaging_slices / 2), 0)),
                                            int(min(round_math(frame + imaging_slices / 2), self.image.n_frames - 1))))
        ref_slices_ind = np.array(range(int(max(round_math(frame - ref_slices / 2), 0)),
                                        int(min(round_math(frame + ref_slices / 2), self.image.n_frames - 1))))

        height, width = self.image.size
        box_x_imaging = width / imaging_zoom * macro_zoom
        box_y_imaging = height / imaging_zoom * macro_zoom
        box_x_ref = width / ref_zoom * macro_zoom
        box_y_ref = height / ref_zoom * macro_zoom
        x_clicked_pixel = width * xyz_clicked['x']
        y_clicked_pixel = height * xyz_clicked['y']
        x_index_imaging = np.s_[int(max(round_math(x_clicked_pixel - box_x_imaging / 2), 0)): int(
            round_math(x_clicked_pixel + box_x_imaging / 2))]
        y_index_imaging = np.s_[int(max(round_math(y_clicked_pixel - box_y_imaging / 2), 0)): int(
            round_math(y_clicked_pixel + box_y_imaging / 2))]
        x_index_ref = np.s_[
                      int(max(round_math(x_clicked_pixel - box_x_ref / 2), 0)): int(
                          round_math(x_clicked_pixel + box_x_ref / 2))]
        y_index_ref = np.s_[
                      int(max(round_math(y_clicked_pixel - box_y_ref / 2), 0)): int(
                          round_math(y_clicked_pixel + box_y_ref / 2))]

        #        image = np.array(self.image.size)
        # get maximum projection of image
        # image = np.array(self.image)
        image = self.controller.settings.get('macro_image')  # use original image
        print('image shape: {}'.format(image.shape))
        # image = np.array(self.image)
        image_imaging_max = np.max(image[imaging_slices_ind, y_index_imaging, x_index_imaging],axis = 0)
        image_ref_max = np.max(image[ref_slices_ind, y_index_ref, x_index_ref],axis = 0)
        # for i in imaging_slices_ind:
        #     self.image.seek(i)
        #     image = np.array(self.image)
        #     image_imaging_max = np.max(np.dstack([image[y_index_imaging, x_index_imaging], image_imaging_max]), axis=2)
        # for i in ref_slices_ind:
        #     self.image.seek(i)
        #     image = np.array(self.image)
        #     image_ref_max = np.max(np.dstack([image[y_index_ref, x_index_ref], image_ref_max]), axis=2)
        image_imaging_max = transform.resize(image_imaging_max, (resolution_x,resolution_y))
        image_ref_max = transform.resize(image_ref_max, (resolution_x,resolution_y))
        #        image_ref = image[yIndex_ref,xIndex_ref]

        #        image_imaging = image[yIndex_imaging,xIndex_imaging]
        #        image_ref = image[yIndex_ref,xIndex_ref]
        self.data['refImages'] = {'imaging': image_imaging_max, 'ref': image_ref_max}


class ScrolledCanvas(tk.Frame):
    def __init__(self, parent, master, controller):
        tk.Frame.__init__(self, parent)
        self.grid(row=0, column=0)
        self.parent = parent
        self.controller = controller
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
