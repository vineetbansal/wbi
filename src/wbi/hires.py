from scipy.io import loadmat
from wbi.file import File


class HiResData(File):
    PATH = "hiResData.mat"

    def __init__(self, *args, **kwargs):
        self.data = loadmat(self.path)["dataAll"]

    def frame_times_delta(self):
        frame_times = self.data[0, 0]["frameTime"].squeeze()
        return frame_times - frame_times[0]

    def flash_times(self):
        flash_time_locations = self.data[0, 0]["flashLoc"].squeeze()
        # Note: flashLoc data is 1-indexed
        flash_times = self.frame_times_delta()[flash_time_locations - 1]
        return flash_times
