import re
import glob
import os.path
import logging
import numpy as np

logger = logging.getLogger(__name__)


class Dat:
    def __init__(self, file_or_folder_path):
        if os.path.isdir(file_or_folder_path):
            dat_files = glob.glob(
                os.path.join(file_or_folder_path, "sCMOS_Frames_*.dat")
            )
            assert (
                len(dat_files) == 1
            ), "Unexpected number of sCMOS_Frames_*.dat files in folder"
            dat_file = dat_files[0]
        else:
            dat_file = file_or_folder_path

        self.dat_file = dat_file
        self._load_other_attributes()

    def _load_other_attributes(self):
        dat_filename = os.path.basename(self.dat_file)
        match = re.match(r"sCMOS_Frames_(\w+)_(\d+)x(\d+).dat", dat_filename)
        assert match is not None
        dtype, rows, cols = match.groups()

        assert dtype == "U16", "Unexpected dtype in dat file"
        self.dtype = {"U16": np.uint16}[dtype]

        self.rows = int(int(rows) / 2)  # rows are R channels + G channels
        self.cols = int(cols)
        self.items_per_stride = self.rows * 2 * self.cols
        self.stride = self.items_per_stride * np.dtype(self.dtype).itemsize

        size_in_bytes = os.stat(self.dat_file).st_size
        self.n_frames = size_in_bytes // self.stride

    def load(self, count=1, offset=0):
        if offset + count > self.n_frames:
            count = self.n_frames - offset
            logger.warning(
                f"Cannot supply {count} frames at offset {offset} when total frames = {self.n_frames}, Reducing to {count}"
            )

        with open(self.dat_file, "rb") as f:
            chunk = np.fromfile(
                f,
                dtype=self.dtype,
                count=count * self.items_per_stride,
                offset=offset * self.stride,
            )
            chunk = chunk.reshape((-1, self.cols, self.rows * 2))
            chunk = np.transpose(chunk, (2, 1, 0))
            return chunk

    def chunks(self, chunk_size=9):
        total_frames = self.n_frames
        for offset in range(0, total_frames, chunk_size):
            count = min(chunk_size, total_frames - offset)
            yield self.load(count=count, offset=offset)
