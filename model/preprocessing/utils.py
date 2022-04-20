"""Module for utility functions for pixel processing."""

import numpy as np
from snappy import Product


def get_band_pixels(band_name: str, prod: Product) -> np.array:
    """
    Returns a numpy array containing the band pixels.
    :param band_name: str. Band name from which to extract the pixels.
    :param prod: Opened product.
    :return: np.array.
    """
    # Extract pixels from band
    band = prod.getBand(band_name)

    # Get band dimensions
    w = band.getRasterWidth()
    h = band.getRasterHeight()

    band_data = np.zeros(w * h, np.float64)  # Initialize empty array filled with 0.
    band.readPixels(0, 0, w, h, band_data)  # Store pixels.
    band_data.shape = h, w  # Reshape array.

    return band_data


def get_bands_pixel_stats(product: Product):
    """
    Gets the stats for every band in the given product. A stat contains the minimal and maximal pixel value that exist
    in a source band.
    :param product: Opened product.
    :return: A dict with the following format: { band_name: [min, max] }
    """
    bands = list(product.getBandNames())

    band_stats = {}
    for b in bands:
        band_data = get_band_pixels(b, product)  # Retrieve band from name.

        stats = [
            np.amin(band_data),
            np.amax(band_data)
        ]
        band_stats[b] = stats

    return band_stats


def selected_max_pixel_value(band: np.ndarray, percent: float = 0.95):
    """
    Returns the maximal pixel value up to which a percent of all pixels are located.
    :param band: np.ndarray. Pixel array.
    :param percent: float, optional. Percent to sum up to and make the cut. Defaults to 0.95.
    :return: float. The max value.
    """
    hist, bins = np.histogram(band, bins="auto")
    hist = hist / band.size  # Convert counting to percent
    sum_ = 0  # Accumulator
    max_ = 0
    for p, m in zip(hist, bins[1:]):
        if sum_ < percent:
            sum_ += p
            max_ = m
        else:
            break
            
    return max_
