import numpy as np
import copy
from scipy import ndimage


# TODO: Add way to convert z_slices to z_um
from app.utilities.math_helpers import compute_drift


class DriftXYZ:

    def __init__(self):
        self.x_pixels = 0
        self.x_um = 0.0
        self.y_pixels = 0
        self.y_um = 0.0
        self.z_slices = 0
        self.z_um = 0.0
        self.focus_list = np.array([])

    def copy(self):
        return copy.deepcopy(self)

    def compute_drift_z(self, image_stack, z_step):
        focus_list = []
        for image_slice in image_stack:
            focus_list.append(self.measure_focus(image_slice))
        focus_list = np.array(focus_list)
        drift_z = focus_list.argmax().item() - np.floor(len(image_stack) / 2)
        self.z_slices = drift_z
        self.focus_list = focus_list
        self.z_um = drift_z * z_step

    @staticmethod
    def measure_focus(image):
        # Gaussian derivative (Geusebroek2000)
        w_size = 15
        nn = np.floor(w_size / 2)
        sig = nn / 2.5
        r = np.arange(-nn.astype(int), nn.astype(int) + 1)
        x, y = np.meshgrid(r, r)
        gg = np.exp(-(x ** 2 + y ** 2) / (2 * sig ** 2)) / (2 * np.pi * sig)
        gx = -x * gg / (sig ** 2)
        gx = gx / np.sum(gx, 1)
        gy = -y * gg / (sig ** 2)
        gy = gy / np.sum(gy)
        ry = ndimage.convolve(image.astype(float), gx, mode='nearest')
        rx = ndimage.convolve(image.astype(float), gy, mode='nearest')
        f_m = rx ** 2 + ry ** 2
        f_m = np.mean(f_m)
        return f_m

    def compute_pixel_drift_x_y(self, img_ref, img):
        shift_x, shift_y = compute_drift(img_ref, img)
        self.x_pixels = shift_x.item()
        self.y_pixels = shift_y.item()

    def scale_x_y_drift_to_image(self, position, zoom, image_shape, drift_params):
        x_multiplier = 1 - 2 * drift_params['invert_drift_x']
        y_multiplier = 1 - 2 * drift_params['invert_drift_y']
        multiplicator = position['scan_voltage_multiplier']
        fov_x_y = position['fov_xy']
        rotation = position['rotation']
        x_y_um = np.squeeze(np.array([self.x_pixels, self.y_pixels])) / image_shape * multiplicator * fov_x_y / zoom
        if rotation != 0:
            sin_a = np.sin(rotation * np.pi / 180.0)
            cos_a = np.cos(rotation * np.pi / 180.0)
            rot_mat = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
            x_y_um = np.dot(rot_mat, x_y_um)
        self.x_um, self.y_um = (x_y_um[0] * x_multiplier, x_y_um[1] * y_multiplier)
