import scipy.io as sio
from wbi.file import File


class Alignment(File):
    PATH = "alignments.mat"

    def __init__(self, *args, **kwargs):
        self._load_mat_file()

    def __getitem__(self, item):
        return self.data[item]

    def _load_mat_file(self):
        alignments_data = sio.loadmat(self.path)["alignments"]

        # Create a two-level dictionary of key: value mappings
        data = {}
        for k in alignments_data.dtype.names:
            data[k] = {}
            inner_names = alignments_data[k][0, 0].dtype.names
            if inner_names is None:
                data[k] = alignments_data[k][0, 0]
            else:
                for k2 in inner_names:
                    data[k][k2] = alignments_data[k][0, 0][k2][0, 0]

        # Does this data have "new-style" points?
        # where labelled points are specific to each frame
        self.has_frame_values = (
            "lowResFluor2BF" in data and "Aall2" in data["lowResFluor2BF"]
        )

        self.data = data
