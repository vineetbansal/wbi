import scipy.io as sio
from wbi.file import File


class Alignment(File):
    PATH = "alignments.mat"

    def __init__(self, *args, **kwargs):
        self._load_mat_file()

    def __getitem__(self, item):
        return self.alignments[item]

    def _load_mat_file(self):
        alignments_data = sio.loadmat(self.path)["alignments"]
        dtypes = {
            names: alignments_data[names][0, 0].dtype.names
            for names in alignments_data.dtype.names
        }
        self.lowResFluor2BF = {
            label: alignments_data["lowResFluor2BF"][0, 0][label][0, 0]
            for label in dtypes["lowResFluor2BF"]
        }
        self.S2AHiRes = {
            label: alignments_data["S2AHiRes"][0, 0][label][0, 0]
            for label in dtypes["S2AHiRes"]
        }
        self.Hi2LowResF = {
            label: alignments_data["Hi2LowResF"][0, 0][label][0, 0]
            for label in dtypes["Hi2LowResF"]
        }
        self.background = alignments_data["background"][0, 0]
        if len(list(self.lowResFluor2BF["Aall"])[0]) < 3:
            self.frames = None
        self.alignments = {
            "lowResFluor2BF": self.lowResFluor2BF,
            "S2AHiRes": self.S2AHiRes,
            "Hi2LowResF": self.Hi2LowResF,
            "background": self.background,
        }
