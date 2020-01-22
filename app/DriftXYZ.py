import numpy as np
import copy
from scipy import ndimage


# TODO: Add way to convert z_slices to z_um
class DriftXYZ:

    def __init__(self):
        self.x_pixels = 0
        self.x_um = 0.0
        self.y_pixels = 0
        self.y_um = 0.0
        self.z_slices = 0
        self.z_um = 0.0
        self.focus_list = np.array([])
        self.x_multiplier = -1
        self.y_multiplier = 1

    def copy(self):
        return copy.deepcopy(self)

    def compute_drift_z(self, image_stack, zstep):
        focus_list = []
        for image_slice in image_stack:
            focus_list.append(self.measure_focus(image_slice))
        focus_list = np.array(focus_list)
        drift_z = focus_list.argmax().item() - np.floor(len(image_stack) / 2)
        self.z_slices = drift_z
        self.focus_list = focus_list
        self.z_um = drift_z * zstep

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
        h, w = img_ref.shape
        fft_ref = np.fft.fft2(img_ref)
        fft_img = np.fft.fft2(img)
        center_y = h / 2
        center_x = w / 2
        prod = fft_ref * np.conj(fft_img)
        cc = np.fft.ifft2(prod)
        max_y, max_x = np.nonzero(np.fft.fftshift(cc) == np.max(cc))
        shift_y = max_y[0] - center_y
        shift_x = max_x[0] - center_x
        # Checks to see if there is an ambiguity problem with FFT because of the
        # periodic boundary in FFT (not sure why or if this is necessary but I'm
        # keeping it around for now)
        if np.abs(shift_y).all() > h / 2:
            shift_y = shift_y - np.sign(shift_y) * h
        if np.abs(shift_x) > h / 2:
            shift_x = shift_x - np.sign(shift_x) * w
        self.x_pixels = shift_x.item()
        self.y_pixels = shift_y.item()

    def scale_x_y_drift_to_image(self, position, zoom, image_shape):
        multiplicator = position['scan_voltage_multiplier']
        fov_x_y = position['fov_xy']
        rotation = position['rotation']
        x_y_um = np.squeeze(np.array([self.x_pixels, self.y_pixels])) / image_shape * multiplicator * fov_x_y / zoom
        if rotation != 0:
            sinA = np.sin(rotation * np.pi / 180.0)
            cosA = np.cos(rotation * np.pi / 180.0)
            rotMat = np.array([[cosA, -sinA], [sinA, cosA]])
            x_y_um = np.dot(rotMat, x_y_um)
        self.x_um, self.y_um = (x_y_um[0] * self.x_multiplier, x_y_um[1] * self.y_multiplier)