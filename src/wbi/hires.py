import os.path
from scipy.io import loadmat


class HiResData:
    def __init__(self, file_or_folder_path):
        if os.path.isdir(file_or_folder_path):
            file_path = os.path.join(file_or_folder_path, "hiResData.mat")
        else:
            file_path = file_or_folder_path

        self.file_path = file_path
        if os.path.exists(file_path):
            self.data = loadmat(self.file_path)["dataAll"]
        else:
            self.data = None

    def frame_times_delta(self):
        frame_times = self.data[0, 0]["frameTime"].squeeze()
        return frame_times - frame_times[0]

    def flash_times(self):
        flash_time_locations = self.data[0, 0]["flashLoc"].squeeze()
        # Note: flashLoc data is 1-indexed
        flash_times = self.frame_times_delta()[flash_time_locations - 1]
        return flash_times
