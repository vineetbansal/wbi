# Misc MATLAB compatibility functions
import numpy as np


# https://stackoverflow.com/questions/40443020
def smooth(a, window_size):
    # a: NumPy 1-D array containing the data to be smoothed
    # window_size: smoothing window size needs, which must be odd number,
    # as in the original MATLAB implementation

    # Note from MATLAB smooth docs:
    # If you specify span as an even number or as a fraction that results in
    # an even number of data points, span is automatically reduced by 1.
    if window_size % 2 == 0:
        window_size -= 1

    out0 = np.convolve(a, np.ones(window_size, dtype=int),
                       'valid') / window_size
    r = np.arange(1, window_size - 1, 2)
    start = np.cumsum(a[:window_size - 1])[::2] / r
    stop = (np.cumsum(a[:-window_size:-1])[::2] / r)[::-1]
    return np.concatenate((start, out0, stop))
