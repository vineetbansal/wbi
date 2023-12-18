import numpy as np
import os
from wbi.experiment import Experiment


def flash_finder(input_folder, output_folder=None, chunksize=9, max_frames=None):
    output_folder = output_folder or input_folder

    experiment = Experiment(input_folder)
    dat = experiment.dat
    timing = experiment.timing

    # TODO: Why are we doing this?
    chunk_max_size = chunksize // 6  # number of frames to read at once
    brightness = np.zeros(dat.n_frames)
    stdev = np.zeros(dat.n_frames)
    index = 0

    for index, chunk in enumerate(dat.chunks(chunk_size=chunk_max_size)):
        chunk = np.transpose(chunk, (2, 1, 0)).reshape(-1, dat.cols * dat.rows * 2)
        brightness[index * chunk_max_size: (index+1) * chunk_max_size] = np.average(chunk, axis=1)
        stdev[index * chunk_max_size: (index + 1) * chunk_max_size] = np.std(chunk.astype(np.float64), axis=1)

    adjusted_brightness = brightness - np.average(brightness)

    # TODO: What is this bfp.txt??
    if os.path.exists(os.path.join(input_folder, "BFP.txt")):
        # TODO: Move Magic number somewhere else
        stdev_brightness = np.std(adjusted_brightness[: index - 12000])
    else:
        stdev_brightness = np.std(adjusted_brightness)

    (repeated_flash_loc,) = np.where(adjusted_brightness > stdev_brightness * 10)

    flash_loc = []
    for index, flash_frame in enumerate(repeated_flash_loc):
        if index == 0:
            flash_loc.append(flash_frame)
        elif flash_frame != repeated_flash_loc[index - 1] + 1:
            flash_loc.append(flash_frame)
    flash_loc = np.array(flash_loc)
