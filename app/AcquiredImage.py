from skimage import io, transform
from PIL import Image
import numpy as np

from app.DriftXYZ import DriftXYZ
from utilities.math_helpers import contrast_stretch


class AcquiredImage:

    def __init__(self):
        self.image_file_path = None
        self.total_chan = None
        self.drift_chan = None
        self.fov_x_y = None
        self.image_stack = np.array([])
        self.is_macro = False
        self.is_reference = False
        self.is_reference_zoomed_out = False
        self.zoom = None
        self.pos_id = 1
        self.drift_x_y_z = DriftXYZ()

    def load(self, settings):
        self.set_zoom(settings)
        self.image_file_path = settings.get('image_file_path')
        self.total_chan = int(settings.get('total_channels'))
        self.drift_chan = int(settings.get('drift_correction_channel'))
        self.fov_x_y = settings.get('fov_x_y')
        image_stack = io.imread(self.image_file_path)
        image_stack = image_stack[np.arange(self.drift_chan - 1, len(image_stack), self.total_chan)]
        self.image_stack = image_stack

    def set_zoom(self, settings):
        if self.is_macro:
            self.zoom = settings.get('macro_zoom')
        elif self.is_reference_zoomed_out:
            self.zoom = settings.get('reference_zoom')
        else:
            self.zoom = settings.get('imaging_zoom')

    def calc_x_y_z_drift(self, reference_max_projection):
        self.drift_x_y_z.compute_drift_z(self.image_stack)
        self.calc_x_y_drift(reference_max_projection)

    def get_max_projection(self):
        return np.max(self.image_stack.copy(), axis=0)

    def calc_x_y_drift(self, reference_max_projection):
        image_max_projection = self.get_max_projection()
        reference_resized = transform.resize(reference_max_projection, image_max_projection.shape)
        self.drift_x_y_z.compute_drift_x_y(reference_resized, image_max_projection)
        self.drift_x_y_z.scale_x_y_drift_to_image(self.fov_x_y, self.zoom, image_max_projection.shape)

    def get_shape(self):
        return self.image_stack.shape


class ReferenceImage(AcquiredImage):

    def __init__(self):
        super(ReferenceImage, self).__init__()
        self.is_reference = True


class ReferenceImageZoomedOut(AcquiredImage):

    def __init__(self, settings):
        super(ReferenceImageZoomedOut, self).__init__()
        self.is_reference_zoomed_out = True


class MacroImage(AcquiredImage):

    def __init__(self):
        super(MacroImage, self).__init__()
        self.is_macro = True
        self.pil_image = None

    def set_image_contrast(self):
        self.image_stack = np.array([contrast_stretch(img) for img in self.image_stack])
        self.image_stack = self.image_stack / np.max(self.image_stack) * 255

    def create_pil_image(self):
        # since PIL doesn't support creating multi-frame images, save the image and load it as a workaround for now.
        image_list = [Image.fromarray(image.astype(np.uint8)) for image in self.image_stack]
        image_list[0].save("../temp/macro_image.tif", compression="tiff_deflate", save_all=True,
                           append_images=image_list[1:])
        self.pil_image = Image.open("../temp/macro_image.tif")
