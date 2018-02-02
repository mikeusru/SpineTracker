import tkinter as tk
from tkinter import ttk
import matplotlib
import numpy as np
from PIL import Image, ImageTk, ImageMath

from guis.PositionsPage import PositionsPage
from utilities.math_helpers import round_math

matplotlib.use("TkAgg")


class MacroWindow(tk.Tk):
    def __init__(self, controller, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)  # initialize regular Tk stuff

        # set properties for main window
        tk.Tk.wm_title(self, "Macro View")
        tk.Tk.geometry(self, newGeometry='700x800+200+200')
        # define container for what's in the window
        self.controller = controller
        self.frame_canvas = ttk.Frame(self)
        self.frame_canvas.grid(row=0, column=0, sticky='nsew')
        self.scrollingCanvas = ScrolledCanvas(self.frame_canvas, self, self.controller)
        self.scale_z = tk.Scale(self.frame_canvas, orient=tk.VERTICAL)
        self.scale_z.grid(row=0, column=2, sticky='ns')
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=2, column=0, sticky='nsew')
        button_load_test_macro_image = ttk.Button(frame_buttons, text="Load Test Macro Image",
                                                  command=lambda: self.load_macro_image())
        button_load_test_macro_image.grid(row=2, column=0, padx=10, pady=10, sticky='nw')
        label_macro_zoom = tk.Label(frame_buttons, text="Macro Zoom", font=controller.get_app_param('large_font'))
        label_macro_zoom.grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        self.macroZoom = tk.StringVar(self)
        entry_macro_zoom = ttk.Entry(frame_buttons, textvariable=self.macroZoom, width=3)
        entry_macro_zoom.grid(row=0, column=1, padx=10, pady=10, sticky='nw')
        self.macroZoom.set(1)
        self.scale_zoom = tk.Scale(self, orient=tk.HORIZONTAL)
        self.scale_zoom.grid(row=1, column=0, sticky='ew')
        self.scale_zoom.config(command=self.change_size, from_=.1, to=5, resolution=.1)
        self.scale_zoom.set(2)
        label_z_slices = tk.Label(frame_buttons, text="Number of Z Slices", font=controller.get_app_param('large_font'))
        label_z_slices.grid(row=1, column=0, padx=10, pady=10, sticky='nw')
        self.num_z_slices = tk.StringVar(self)
        self.num_z_slices.set(10)
        entry_z_slices = ttk.Entry(frame_buttons, textvariable=self.num_z_slices, width=4)
        entry_z_slices.grid(row=1, column=1, padx=10, pady=10, sticky='nw')
        button_load_macro_image = ttk.Button(frame_buttons, text="Grab Macro Image",
                                             command=lambda: self.load_macro_image())
        button_load_macro_image.grid(row=2, column=1, padx=10, pady=10, sticky='nw')
        self.image = controller.acq['imageStack']
        self.slice_index = 0

    def change_size(self):
        try:
            self.image
        except:
            return
        self.scrollingCanvas.setImage()

    def load_macro_image(self):
        if self.get_app_param('simulation'):
            self.image = Image.open("../testing/macroImage.tif")
            self.controller.centerXY = (0, 0)
        else:
            # set zoom
            macro_zoom = float(self.macroZoom.get())
            self.controller.set_zoom(macro_zoom)
            # set Z slice number
            z_slice_num = float(self.num_z_slices.get())
            self.controller.set_z_slice_num(z_slice_num)
            # grab stack
            self.controller.grab_stack()
            self.controller.load_acquired_image(updateFigure=False)
            self.image = self.controller.acq['imageStack']
            # get the motor coordinates
            self.controller.get_current_position()
            x, y, z = self.currentCoordinates
            self.controller.centerXY = (x, y)

        self.multi_slice_viewer()

    def multi_slice_viewer(self):

        self.scale_z.config(command=self.scale_callback, from_=0, to=self.image.n_frames - 1)
        self.slice_index = self.image.n_frames // 2
        self.scale_z.set(self.slice_index)
        self.scrollingCanvas.setImage()

    def scale_callback(self, event):
        self.slice_index = self.scale_z.get()
        self.scrollingCanvas.setImage()

    def add_position_on_imagee_click(self, x, y, z):
        # translate to normal coordinates
        fovX, fovY = self.controller.settings['fovXY']
        # xy currently originate from top left of image.
        # translate them to coordinate plane directionality.
        # also, make them originate from center
        x_center, y_center = self.controller.centerXY
        xyz_clicked = {'x': x, 'y': y, 'z': z}
        x = x - .5
        y = -y + .5
        # translate coordinates to µm
        x = x * fovX + x_center
        y = y * fovY + y_center
        # add coordinates to position table
        print('x, y, z = {0}, {1}, {2}'.format(x, y, z))
        xyz = {'x': x, 'y': y, 'z': z}
        self.get_ref_images_from_macro(xyz_clicked)
        self.controller.add_position(self.controller.frames[PositionsPage], xyz=xyz, refImages=self.refImages)

    def get_ref_images_from_macro(self, xyz_clicked):
        macro_zoom = float(self.macroZoom.get())
        imaging_zoom = float(self.controller.frames[PositionsPage].imagingZoom.get())
        ref_zoom = float(self.controller.frames[PositionsPage].refZoom.get())
        imaging_slices = int(self.controller.frames[PositionsPage].imagingSlices.get())
        ref_slices = int(self.controller.frames[PositionsPage].refSlices.get())

        frame = self.slice_index
        imagingSlices_ind = range(int(round_math(frame - imaging_slices / 2)),
                                  int(round_math(frame + imaging_slices / 2)))
        refSlices_ind = range(int(round_math(frame - ref_slices / 2)), int(round_math(frame + ref_slices / 2)))

        height, width = self.image.size
        boxX_imaging = width / imaging_zoom * macro_zoom
        boxY_imaging = height / imaging_zoom * macro_zoom
        boxX_ref = width / ref_zoom * macro_zoom
        boxY_ref = height / ref_zoom * macro_zoom
        x_clicked_pixel = width * xyz_clicked['x']
        y_clicked_pixel = height * xyz_clicked['y']
        xIndex_imaging = np.s_[int(round_math(x_clicked_pixel - boxX_imaging / 2)): int(
            round_math(x_clicked_pixel + boxX_imaging / 2))]
        yIndex_imaging = np.s_[int(round_math(y_clicked_pixel - boxY_imaging / 2)): int(
            round_math(y_clicked_pixel + boxY_imaging / 2))]
        xIndex_ref = np.s_[
                     int(round_math(x_clicked_pixel - boxX_ref / 2)): int(round_math(x_clicked_pixel + boxX_ref / 2))]
        yIndex_ref = np.s_[
                     int(round_math(y_clicked_pixel - boxY_ref / 2)): int(round_math(y_clicked_pixel + boxY_ref / 2))]

        #        image = np.array(self.image.size)
        # get maximum projection of image
        image = np.array(self.image)
        image_imaging_max = image[yIndex_imaging, xIndex_imaging]
        image_ref_max = image[yIndex_ref, xIndex_ref]
        for i in imagingSlices_ind:
            self.image.seek(i)
            image = np.array(self.image)
            image_imaging_max = np.max(np.dstack([image[yIndex_imaging, xIndex_imaging], image_imaging_max]), axis=2)
        for i in refSlices_ind:
            self.image.seek(i)
            image = np.array(self.image)
            image_ref_max = np.max(np.dstack([image[yIndex_ref, xIndex_ref], image_ref_max]), axis=2)

        #        image_ref = image[yIndex_ref,xIndex_ref]

        #        image_imaging = image[yIndex_imaging,xIndex_imaging]
        #        image_ref = image[yIndex_ref,xIndex_ref]
        self.refImages = {'imaging': image_imaging_max, 'ref': image_ref_max}


class ScrolledCanvas(tk.Frame):
    def __init__(self, parent, master, controller):
        tk.Frame.__init__(self, parent)
        self.grid(row=0, column=0)
        self.parent = parent
        self.controller = controller
        self.master = master
        canv = tk.Canvas(self, relief=tk.SUNKEN)
        canv.bind('<Button-3>', func=self.canvasRightClick)
        canv.config(width=600, height=600)
        canv.config(highlightthickness=0)

        sbarV = tk.Scrollbar(self, orient=tk.VERTICAL)
        sbarH = tk.Scrollbar(self, orient=tk.HORIZONTAL)

        sbarV.config(command=canv.yview)
        sbarH.config(command=canv.xview)

        canv.config(yscrollcommand=sbarV.set)
        canv.config(xscrollcommand=sbarH.set)

        sbarV.grid(row=0, column=1, sticky='ns')
        sbarH.grid(row=1, column=0, sticky='ew')

        canv.grid(row=0, column=0, sticky='nsew')
        self.canvas = canv

    def canvasRightClick(self, event):
        # Create popup menu
        w, h = self.master.image.size
        canvas = event.widget
        x = canvas.canvasx(event.x) / (w * self.master.scale_zoom.get())
        y = canvas.canvasy(event.y) / (h * self.master.scale_zoom.get())
        if x > 1 or y > 1:
            return
        z = self.master.sliceIndex
        #            print('eventx, eventy = {0}, {1}'.format(event.x,event.y))
        #            print(canvas.find_closest(x,y))
        self.popup = tk.Menu(self, tearoff=0)
        self.popup.add_command(label='Add Position', command=lambda: self.master.add_position_on_imagee_click(x, y, z))
        # display the popup menu
        self.popup.post(event.x_root, event.y_root)

    def setImage(self):
        im = self.master.image
        frame = self.master.sliceIndex
        zoom = self.master.scale_zoom.get()
        width, height = im.size
        width_r = round(width * zoom)
        height_r = round(height * zoom)
        im.seek(frame)  # move to appropriate frame
        # rescale to uint8 for accurate display in TkInter
        im_max = np.array(im).max()
        im = ImageMath.eval("float(a)", a=im)
        im = ImageMath.eval("convert(a/a_m * 255, 'L')", a=im, a_m=im_max)
        self.im_r = im.resize((width_r, height_r))
        self.canvas.config(scrollregion=(0, 0, width_r, height_r))
        self.im2 = ImageTk.PhotoImage(master=self.canvas, image=self.im_r)
        self.imgtag = self.canvas.create_image(0, 0, anchor="nw", image=self.im2)
