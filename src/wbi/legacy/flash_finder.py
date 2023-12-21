import numpy as np
import os
from scipy.io import savemat

def flash_finder(input_folder, experiment, output_folder=None, chunk_size=4000, max_frames=None):
    output_folder = output_folder or input_folder

    experiment = experiment
    dat = experiment.dat
    timing = experiment.timing

    # TODO: Why are we doing this?
    chunk_max_size = chunk_size // 6  # number of frames to read at once
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

    x_pos, y_pos, z_pos = experiment.configure_frame_positions()
    volume_index = experiment.configure_frame_timings(input_folder)

    matlab_dict = {}
    data_all = {
    "imageIdx": timing.timing["frame_index"].values.reshape(timing.timing["frame_index"].shape[0], 1),
    "frameTime": timing.timing["time"].values.reshape(timing.timing["time"].shape[0], 1),
    "flashLoc": (flash_loc + 1).reshape(flash_loc.shape[0], 1),
    "stackIdx": (volume_index + 1).reshape(volume_index.shape[0], 1),
    "imSTD": stdev.reshape(stdev.shape[0], 1),
    "imAvg": brightness.reshape(brightness.shape[0], 1),
    "xPos": x_pos.reshape(x_pos.shape[0], 1),
    "yPos": y_pos.reshape(y_pos.shape[0], 1),
    "Z": z_pos.reshape(z_pos.shape[0], 1)
    }

    matlab_dict["dataAll"] = data_all

    savemat(os.path.join(output_folder, "hiResData.mat"), matlab_dict)

    with open(os.path.join(output_folder, "submissionParameters.txt"), "w") as f:
        f.write(f"NFrames {volume_index[-1]}")
