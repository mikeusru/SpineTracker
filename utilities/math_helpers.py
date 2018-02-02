import math
from scipy import ndimage
import numpy as np

def round_math(n, ndigits=0):
    part = n * 10 ** ndigits
    delta = part - int(part)
    # always round "away from 0"
    if delta >= 0.5 or -0.5 < delta <= 0:
        part = math.ceil(part)
    else:
        part = math.floor(part)
    return part / (10 ** ndigits)

def floatOrNone(x):
    if x == "":
        y = None
    else:
        y = float(x)
    return y


def floatOrZero(x):
    if x == "":
        y = 0.0
    else:
        y = float(x)
    return y


def focusMeasure(image):
    # Gaussian derivative (Geusebroek2000)
    w_size = 15
    N = np.floor(w_size / 2)
    sig = N / 2.5
    r = np.arange(-N.astype(int), N.astype(int) + 1)
    x, y = np.meshgrid(r, r)
    G = np.exp(-(x ** 2 + y ** 2) / (2 * sig ** 2)) / (2 * np.pi * sig)
    Gx = -x * G / (sig ** 2)
    Gx = Gx / np.sum(Gx, 1)
    Gy = -y * G / (sig ** 2)
    Gy = Gy / np.sum(Gy)
    Ry = ndimage.convolve(image.astype(float), Gx, mode='nearest')
    Rx = ndimage.convolve(image.astype(float), Gy, mode='nearest')
    FM = Rx ** 2 + Ry ** 2
    FM = np.mean(FM)
    return FM



# output is directional shift [x,y] in pixels. based on Sugar et al (2014) paper
def computeDrift(imgref, img):
    h, w = imgref.shape
    fft_ref = np.fft.fft2(imgref)
    fft_img = np.fft.fft2(img)
    centery = h / 2
    centerx = w / 2
    prod = fft_ref * np.conj(fft_img)
    cc = np.fft.ifft2(prod)
    maxy, maxx = np.nonzero(np.fft.fftshift(cc) == np.max(cc))
    shifty = maxy - centery
    shiftx = maxx - centerx
    # Checks to see if there is an ambiguity problem with FFT because of the
    # periodic boundary in FFT (not sure why or if this is necessary but I'm
    # keeping it around for now)
    if np.abs(shifty) > h / 2:
        shifty = shifty - np.sign(shifty) * h
    if np.abs(shiftx) > h / 2:
        shiftx = shiftx - np.sign(shiftx) * w

    return {'shiftx': shiftx[0], 'shifty': shifty[0]}