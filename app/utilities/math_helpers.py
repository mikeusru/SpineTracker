import math
import numpy as np
from skimage import exposure


def round_math(n, n_digits=0):
    part = n * 10 ** n_digits
    delta = part - int(part)
    # always round "away from 0"
    if delta >= 0.5 or -0.5 < delta <= 0:
        part = math.ceil(part)
    else:
        part = math.floor(part)
    return part / (10 ** n_digits)


def blank_to_none(var):
    if isinstance(var, str) and (var == ""):
        return None
    else:
        return var


def blank_to_zero(var):
    if isinstance(var, str) and (var == ""):
        return 0
    else:
        return var


def none_to_blank(var):
    if var is None:
        return ""
    else:
        return var


# output is directional shift [x,y] in pixels. based on Sugar et al (2014) paper
# TODO: instead of having an output, this function can be moved directly to save shiftxy in main program
def compute_drift(img_ref, img):
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
    return shift_x, shift_y


def contrast_stretch(img):
    p2, p98 = np.percentile(img, (2, 98))
    return exposure.rescale_intensity(img, in_range=(p2, p98))
