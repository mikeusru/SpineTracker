from skimage import io, transform
from PIL import Image
import numpy as np
import copy

from app.DriftXYZ import DriftXYZ
from app.utilities.math_helpers import contrast_stretch

from app.Position import Position


class AcquiredImage:

    def __init__(self):
        self.image_file_path = None
        self.total_chan = None
        self.drift_chan = None
        self.image_stack = np.array([])
        self.is_macro = False
        self.is_reference = False
        self.is_reference_zoomed_out = False
        self.zoom = 10.0
        self.af_xywh = None
        self.pos_id = 1
        self.drift_x_y_z = DriftXYZ()
        self.position = Position()

    def copy(self):
        return copy.deepcopy(self)

    def load(self, settings, pos_id, position=None):
        if position is None:
            self.position['scan_voltage_multiplier'] = np.array(settings.get('scan_voltage_multiplier'))
            self.position['rotation'] = float(settings.get('rotation'))
            self.position['fov_xy'] = np.squeeze(np.array([settings.get('fov_x'), settings.get('fov_y')]))
            self.position['zstep'] = float(settings.get('zstep'))
            self.position['zoom'] = float(settings.get('current_zoom'))
        else:
            self.position['scan_voltage_multiplier'] = position['scan_voltage_multiplier']
            self.position['rotation'] = position['rotation']
            self.position['fov_xy'] = position['fov_xy']
            self.position['zstep'] = position['zstep']
            self.position['zoom'] = position['zoom']

        self.set_zoom(settings)
        self.image_file_path = settings.get('image_file_path')
        self.total_chan = int(settings.get('total_channels'))
        self.drift_chan = int(settings.get('drift_correction_channel'))
        self.pos_id = pos_id
        image_stack = io.imread(self.image_file_path)
        image_stack = self._set_correct_dimensions(image_stack)
        image_stack = image_stack[np.arange(self.drift_chan - 1, len(image_stack), self.total_chan)]
        self.image_stack = image_stack
        return image_stack

    def _set_correct_dimensions(self, image_stack):
        if len(image_stack.shape) == 2:
            image_stack = np.expand_dims(image_stack, axis=0)
        image_stack = self.correct_for_3_channel_image_bug(image_stack)
        return image_stack

    @staticmethod
    def correct_for_3_channel_image_bug(image_stack):
        if (image_stack.shape[2] == 3) or (image_stack.shape[2] == 4):
            image_stack = np.moveaxis(image_stack, -1, 0)
        return image_stack

    def set_zoom(self, settings):
        if self.is_macro:
            self.zoom = settings.get('macro_zoom')
        elif self.is_reference_zoomed_out:
            self.zoom = settings.get('reference_zoom')
        else:
            self.zoom = settings.get('imaging_zoom')

    def calc_x_y_z_drift(self, position, zoom, reference_max_projection, drift_params):
        # TODO: Cut section of image stack based on ROI position

        # TODO: Make this section µm-based for reference image
        # TODO: and based on the size of the ref image in the center of the zoomed out ref image
        z_stack = self.get_cropped_z_stack()
        self.drift_x_y_z.compute_drift_z(z_stack, position['zstep'])
        self.calc_x_y_drift(position, zoom, reference_max_projection, drift_params)

    def get_cropped_z_stack(self):
        z_stack = self.image_stack
        if self.af_xywh:
            z_stack = self.image_stack[
                      self.af_xywh[0]: self.af_xywh[1] + self.af_xywh[3],
                      self.af_xywh[0]: self.af_xywh[0]+self.af_xywh[2]
                      ]
            return z_stack

    def get_max_projection(self):
        return np.max(self.image_stack.copy(), axis=0)

    def calc_x_y_drift(self, position, zoom, reference_max_projection, drift_params):
        image_max_projection = self.get_max_projection()
        reference_resized = transform.resize(reference_max_projection, image_max_projection.shape)
        self.drift_x_y_z.compute_pixel_drift_x_y(reference_resized, image_max_projection)
        self.drift_x_y_z.scale_x_y_drift_to_image(position, zoom,
                                                  image_max_projection.shape, drift_params)  # This actually requires voltage_mult and rotation.

    def get_shape(self):
        return self.image_stack.shape

    def set_stack(self, image_stack):
        self.image_stack = image_stack

    def set_af_xywh(self, xywh):
        self.af_xywh = xywh


class ReferenceImage(AcquiredImage):

    def __init__(self):
        super(ReferenceImage, self).__init__()
        self.is_reference = True


class ReferenceImageZoomedOut(AcquiredImage):

    def __init__(self):
        super(ReferenceImageZoomedOut, self).__init__()
        self.is_reference_zoomed_out = True


class MacroImage(AcquiredImage):

    def __init__(self):
        super(MacroImage, self).__init__()
        self.is_macro = True
        self.pil_image = None
        self.temp_file_path = "../temp/macro_image.tif"
        self.found_spines = None

    def set_image_contrast(self):
        self.image_stack = np.array([contrast_stretch(img) for img in self.image_stack])
        self.image_stack = self.image_stack / np.max(self.image_stack) * 255

    def create_pil_image(self):
        # since PIL doesn't support creating multi-frame images, save the image and load it as a workaround for now.
        image_list = [Image.fromarray(image.astype(np.uint8)) for image in self.image_stack]
        image_list[0].save(self.temp_file_path, compression="tiff_deflate", save_all=True,
                           append_images=image_list[1:])
        self.pil_image = Image.open(self.temp_file_path)
