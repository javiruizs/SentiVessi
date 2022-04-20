"""Module exclusively for image formatting functions."""
import numpy as np

from model.preprocessing.utils import selected_max_pixel_value


def simple_scale_pixels(image: np.ndarray, max_val: float = 255) -> np.array:
    """Scales the pixels to the value specified by max_val. It assumes minimal pixel value is 0.

    :param image: 1-D pixel array.
    :param max_val: Optional. Maximal value. Defaults to 255.
    :return: Converted pixel array. Dtype is uint8.
    """
    return (image / np.amax(image) * max_val).astype("uint8")


def clip_scale_pixels(image: np.ndarray, cmin: float = 0, cmax: float = 1, max_val: float = 255) -> np.array:
    """Clips the pixels between [cmin, cmax]. Then, they are multiplied by max_val.

    :param image: 1-D pixel array.
    :param cmin: Clipping minimal.
    :param cmax: Clipping maximal.
    :param max_val: Value to multiply.
    :return: Converted pixel array. Dtype is uint8.
    """

    return (np.clip(image, cmin, cmax) * max_val).astype("uint8")


def clip_scale_percent_pixels(image: np.ndarray, percent: float = 0.95, max_val: int = 255):
    """
    Clip-scales the pixel values between 0 and the value up to which the given percent of pixels are located.
    :param image: np.ndarray. Pixel array.
    :param percent: float, optional. Percent of pixels to clip-scale. Defaults to 0.95.
    :param max_val: int, optional. Value to convert the maximum value. Defaults to 255.
    :return: np.ndarray. Clip-scaled image pixel array.
    """
    imgs = []
    for i in range(image.shape[2]):
        img = image[:, :, i].copy()
        cmax = selected_max_pixel_value(img, percent)
        img = np.clip(img, 0, cmax)
        img /= cmax
        img *= max_val
        imgs.append(img)
    return np.dstack(imgs).astype("uint8")


def logarithmic_scale(pixels: np.ndarray, amplitude: int = 20, positive: bool = True) -> np.array:
    """Converts an array of pixels to the logarithmic scale.

    :param pixels: Pixel array.
    :param amplitude: Optional. Amplitude. Defaults to 20. Other usual values: 10.
    :param positive: Optional. If set, data will be shifted to the positive axis.
        This means that the minimum value will be added to all elements.
    :return: The converted numpy array. Conversion is not inplace.
    """
    log10 = np.log10(pixels + 1) * amplitude
    return log10 + np.min(pixels) if positive else log10
