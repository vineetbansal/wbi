import numpy as np
import pandas as pd
from wbi import config
from wbi.file import File


class Timing(File):
    PATH = "framesDetails.txt"

    def __init__(self, *args, **kwargs):
        self._load_timing_file()

    def _load_timing_file(self):
        timing = pd.read_csv(self.path, sep="\t")
        assert list(timing.columns) == [
            "Timestamp",
            "frameCount",
        ], "Unexpected columns in timing file"

        # Simplify column names
        timing.columns = ["time", "frame"]

        timing = timing.sort_values(by="frame")

        # sometimes "frame" jumps by +2 in one step and then by 0 in the next
        # one; make it so that it jumps by +1 in both these steps
        frame = timing["frame"]
        mask = (frame.diff() == 2) & (frame.diff(-1) == 0)
        frame[mask][:] -= 1

        timing = timing.sort_values(by="frame")

        # frame_index = 1 .. n
        timing["frame_index"] = timing["frame"] - timing["frame"].min() + 1
        timing["frame_index_diff"] = timing["frame_index"].diff()

        # frame_chunk = 1 .. m, indicating a contiguous set of frames
        median_frame_index_diff = timing["frame_index_diff"].median()
        timing["_chunk"] = (
            timing["frame_index_diff"] > (10 * median_frame_index_diff)
        ).cumsum()

        timing["dc_offset"] = 5.0  # TODO: ??
        timing["stddev"] = 1.0

        # Save the original row indices (since these correspond to the slices
        # of the Dat object in order, and then change the index for fast
        # joins with other DataFrames with corresponding "frame" information
        timing["_original_row_index"] = np.arange(len(timing))
        timing.set_index("frame", drop=False, inplace=True)

        self.timing = timing
        self.n_chunks = timing["_chunk"].max() + 1

    def __len__(self):
        return len(self.timing)

    def get_start_end_row_indices(self, chunk):
        chunk_timing = self.timing[self.timing["_chunk"] == chunk]
        row_min = int(chunk_timing["_original_row_index"].min())
        row_max = int(chunk_timing["_original_row_index"].max())
        return row_min, row_max

    def merge_sync(self, sync):
        df = self.timing.join(sync.sync, how="left", lsuffix="_l", rsuffix="_r")

        # Interpolate NaN values
        for col in ("ludl_x", "ludl_y", "piezo_position"):
            df[col] = df[col].interpolate(method="linear")

        window_size = config.flash_finder.piezo_smoothing_window_size
        piezo_position = np.convolve(
            df["piezo_position"], np.full(window_size, 1 / window_size), mode="same"
        )
        df["piezo_position_smoothed"] = piezo_position

        # volume_direction is in {-1, 0, +1}. In very rare cases it will be 0.
        # Note the `append` as we wish to retain the appropriate number of
        # volume_direction values (the length of df).
        volume_direction = np.sign(np.diff(piezo_position, prepend=piezo_position[0]))

        # Convert to {0, 1}. Treat the rare 0 case as 0 (piezo voltage is at an
        # inflexion point so it doesn't really matter).
        volume_direction = (volume_direction + 1) // 2

        # The volume direction where we were not able to smooth out piezo_position
        # (boundary of size window_size) are assumed to be the same as what we observe
        # immediately before/after the window
        volume_direction[: window_size + 1] = volume_direction[window_size + 1]
        volume_direction[-window_size:] = volume_direction[-window_size - 1]
        df["volume_direction"] = volume_direction

        # volume_index is 0-indexed and increments anytime volume_direction
        # goes from 0->1 or 1->0
        df["volume_index"] = np.cumsum(
            np.abs(np.diff(volume_direction, prepend=volume_direction[0]))
        ).astype(int)

        return df


class LowMagTiming(File):
    PATH = "CamData.txt"

    def __init__(self, *args, **kwargs):
        self.has_stage_data = False
        self._load_timing_file()

    def __len__(self):
        return len(self.timing)

    def _load_timing_file(self):
        timing = pd.read_csv(self.path, sep="\t")
        if len(timing.columns) == 2:
            assert list(timing.columns) == [
                "Total Frames",
                "Time",
            ], "Unexpected columns in timing file"

            # Simplify column names
            timing.columns = ["frame", "time"]
        else:
            # Recently added stage position x/y columns
            assert len(timing.columns) == 4
            assert list(timing.columns)[:2] == [
                "Total Frames",
                "Time",
            ], "Unexpected columns in timing file"
            self.has_stage_data = True
            timing.columns = ["frame", "time", "stage_x", "stage_y"]

        # 0..n-1 => 1..n
        timing["frame"] = timing["frame"] + 1

        self.timing = timing

    def fix_repeats(self):
        """
        add fix to deal with occasional repeat times, unique times are required
        for alignments, this will tend to make then unique

        From AviFlashAlign_v2.m
        TODO: The logic here doesn't make sense! Later time values are
        distorted more than the earlier ones.
        """
        time = self.timing["time"]
        time = time + np.mean(np.diff(time)) * 0.001 * np.arange(1, len(time) + 1)
        self.timing["time"] = time

    def time_deltas(self):
        return (self.timing["time"] - self.timing["time"].iloc[0]).to_numpy()


class FrameSynchronous(File):
    PATH = "other-frameSynchronous.txt"

    def __init__(self, *args, **kwargs):
        self._load_sync_file()

    def _load_sync_file(self):
        sync = pd.read_csv(self.path, sep="\t", index_col=False)
        assert list(sync.columns) == [
            "Frame index",
            "Piezo position (V)",
            "Piezo direction (+-1)",
            "Volume index",
            "Ludl X",
            "Ludl Y",
        ], "Unexpected columns in timing file"

        # Simplify column names
        sync.columns = [
            "frame",
            "piezo_position",
            "piezo_direction",
            "volume_index",
            "ludl_x",
            "ludl_y",
        ]

        sync = sync.sort_values(by="frame").drop_duplicates(
            subset="frame", keep="first"
        )

        sync.set_index("frame", drop=False, inplace=True)

        self.sync = sync

    def __len__(self):
        return len(self.sync)
