import os
import pandas as pd


class Timing:
    def __init__(self, file_or_folder_path):
        if os.path.isdir(file_or_folder_path):
            timing_file = os.path.join(file_or_folder_path, "framesDetails.txt")
        else:
            timing_file = file_or_folder_path

        self.timing_file = timing_file
        self._load_timing_file()

    def _load_timing_file(self):
        timing = pd.read_csv(self.timing_file, sep="\t")
        assert list(timing.columns) == [
            "Timestamp",
            "frameCount",
        ], "Unexpected columns in timing file"

        # Simplify column names
        timing.columns = ["time", "frame"]

        timing = timing.sort_values(by="frame").drop_duplicates(
            subset="frame", keep=False
        )
        # frame_index = 1 .. n
        timing["frame_index"] = timing["frame"] - timing["frame"].min() + 1
        timing["frame_index_diff"] = timing["frame_index"].diff()

        # frame_chunk = 1 .. m, indicating a contiguous set of frames
        median_frame_index_diff = timing["frame_index_diff"].median()
        timing["chunk"] = (
            timing["frame_index_diff"] > (10 * median_frame_index_diff)
        ).cumsum()

        timing["dc_offset"] = 5.0  # TODO: ??
        timing["stddev"] = 1.0

        self.timing = timing
        self.n_chunks = timing["chunk"].max() + 1

    def __len__(self):
        return len(self.timing)

    def get_start_end_row_indices(self, chunk):
        chunk_timing = self.timing[self.timing["chunk"] == chunk]
        return chunk_timing.index.min(), chunk_timing.index.max()


class LowMagTiming:
    def __init__(self, file_or_folder_path):
        if os.path.isdir(file_or_folder_path):
            timing_file = os.path.join(file_or_folder_path, "CamData.txt")
            assert os.path.exists(timing_file), f"{timing_file} not found"
        else:
            timing_file = file_or_folder_path

        self.timing_file = timing_file
        self._load_timing_file()

    def __len__(self):
        return len(self.timing)

    def _load_timing_file(self):
        timing = pd.read_csv(self.timing_file, sep="\t")
        assert list(timing.columns) == [
            "Total Frames",
            "Time",
        ], "Unexpected columns in timing file"

        # Simplify column names
        timing.columns = ["frame", "time"]

        # 0..n-1 => 1..n
        timing["frame"] = timing["frame"] + 1

        self.timing = timing
