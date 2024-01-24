import scipy.io as sio
from wbi.file import File


class Alignment(File):
    PATH = "alignments.mat"

    def __init__(self, *args, **kwargs):
        # TODO: This needs to be updated after the initialization of alignment class
        self.load_mat_file = args[1] if len(args) > 1 else False
        if self.load_mat_file:
            self._load_mat_file()

    def __getitem__(self, item):
        return self.coordinates[item]

    def _load_mat_file(self):
        alignments_data = sio.loadmat(self.path)["alignments"]
        image_channels = {
            names: alignments_data[names][0, 0].dtype.names
            for names in alignments_data.dtype.names
        }
        self.coordinates = {
            "lowResFluor2BF": {
                channel: alignments_data["lowResFluor2BF"][0, 0][channel][0, 0]
                for channel in image_channels["lowResFluor2BF"]
            },
            "S2AHiRes": {
                channel: alignments_data["S2AHiRes"][0, 0][channel][0, 0]
                for channel in image_channels["S2AHiRes"]
            },
            "Hi2LowResF": {
                channel: alignments_data["Hi2LowResF"][0, 0][channel][0, 0]
                for channel in image_channels["Hi2LowResF"]
            },
            "background": alignments_data["background"][0, 0],
        }
        self.has_frame_values = "Aall2" in self.coordinates["lowResFluor2BF"]
