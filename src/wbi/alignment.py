import scipy.io as sio
from wbi.file import File


class Alignment(File):
    PATH = "alignments.mat"

    def __init__(self, *args, **kwargs):
        self._load_mat_file()

    def _load_mat_file(self):
        alignments_data = sio.loadmat(self.path)["alignments"]
        dtypes = {
            names: alignments_data[names][0, 0].dtype.names
            for names in alignments_data.dtype.names
        }
        self.lowResFluor2BF = [
            alignments_data["lowResFluor2BF"][0, 0][val][0, 0]
            for val in dtypes["lowResFluor2BF"]
        ]
        self.S2AHiRes = [
            alignments_data["S2AHiRes"][0, 0][val][0, 0] for val in dtypes["S2AHiRes"]
        ]
        self.Hi2LowResF = [
            alignments_data["Hi2LowResF"][0, 0][val][0, 0]
            for val in dtypes["Hi2LowResF"]
        ]
        self.background = alignments_data["background"][0, 0]
