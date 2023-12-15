import os.path
import tempfile
from scipy.io import loadmat
from wbi.legacy.make_centerline import make_centerline


def test_make_centerline(data_folder):
    max_frames = 3
    with tempfile.TemporaryDirectory() as temp_dir:
        output_folder = temp_dir
        _ = make_centerline(
            input_folder=data_folder,
            output_folder=output_folder,
            max_frames=max_frames,
            plot=True,
        )

        centerline_mat = loadmat(os.path.join(output_folder, "centerline.mat"))

        center_line = centerline_mat["centerline"]
        assert center_line.shape == (100, 2, 3)

        eigenProj = centerline_mat["eigenProj"]
        assert eigenProj.shape == (6, 3)

        worm_centered = centerline_mat["wormcentered"]
        assert worm_centered.shape == (99, 3)
