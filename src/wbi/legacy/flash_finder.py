import numpy as np
from wbi.experiment import Experiment


def flash_finder(input_folder, output_folder=None, chunksize=4000, max_frames=None):
    output_folder = output_folder or input_folder

    experiment = Experiment(input_folder)
    dat = experiment.dat

    # TODO: Why are we doing this?
    chunk_max_size = chunksize // 6  # number of frames to read at once
    brightness = np.zeros(dat.n_frames)
    stdev = np.zeros(dat.n_frames)

    for index, chunk in enumerate(dat.chunks(chunk_size=chunk_max_size)):
        chunk = np.transpose(chunk, (2, 1, 0)).reshape(-1, dat.cols * dat.rows * 2)
        brightness[index * chunk_max_size: (index+1) * chunk_max_size] = np.average(chunk, axis=1)
        stdev[index * chunk_max_size: (index + 1) * chunk_max_size] = np.std(chunk.astype(np.float64), axis=1)

