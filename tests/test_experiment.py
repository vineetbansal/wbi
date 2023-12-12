import tempfile
import os.path
from wbi.experiment import Experiment


def test_experiment(data_folder):
    experiment = Experiment(data_folder)
    assert experiment.timing
    assert experiment.dat
    assert experiment.dat.rows == 512
    assert experiment.dat.cols == 512

    with tempfile.TemporaryDirectory() as temp_dir:
        output_folder = temp_dir
        experiment.generate_median_images(output_folder=output_folder)

        assert os.path.exists(os.path.join(output_folder, "dat_1.tif"))
        for i in range(1, 18):
            assert os.path.exists(os.path.join(output_folder, f"cam1_{i}"))
