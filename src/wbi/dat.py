import re
import os.path
import logging
import numpy as np
from wbi.file import File

logger = logging.getLogger(__name__)


class Dat(File):
    PATH = "sCMOS_Frames_*.dat"

    def __init__(self, *args, **kwargs):
        self._load_other_attributes()

    def _load_other_attributes(self):
        dat_filename = os.path.basename(self.path)
        match = re.match(r"sCMOS_Frames_(\w+)_(\d+)x(\d+).dat", dat_filename)
        assert match is not None
        dtype, rows, cols = match.groups()

        assert dtype == "U16", "Unexpected dtype in dat file"
        self.dtype = {"U16": np.uint16}[dtype]

        self.rows = int(int(rows) / 2)  # rows are R channels + G channels
        self.cols = int(cols)
        self.items_per_stride = self.rows * 2 * self.cols
        self.stride = self.items_per_stride * np.dtype(self.dtype).itemsize

        size_in_bytes = os.stat(self.path).st_size
        self.n_frames = size_in_bytes // self.stride

    def load(self, count=1, offset=0):
        if offset + count > self.n_frames:
            count = self.n_frames - offset
            logger.warning(
                f"Cannot supply {count} frames at offset {offset} when total frames = {self.n_frames}, Reducing to {count}"
            )

        with open(self.path, "rb") as f:
            chunk = np.fromfile(
                f,
                dtype=self.dtype,
                count=count * self.items_per_stride,
                offset=offset * self.stride,
            )
            chunk = chunk.reshape((-1, self.cols, self.rows * 2))
            chunk = np.transpose(chunk, (2, 1, 0))
            return chunk

    def chunks(self, chunk_size=4000, max_frames=None):
        total_frames = (
            self.n_frames if max_frames is None else min(max_frames, self.n_frames)
        )
        for offset in range(0, total_frames, chunk_size):
            count = min(chunk_size, total_frames - offset)
            yield self.load(count=count, offset=offset)
