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


def test_flash_finder(data_folder):
    # input_folder needs to have
    #   sCMOS_Frames_U16_1024x512.dat or frames_U16_1024x512.dat
    #   BFP.txt (optional)
    #   framesDetails.txt
    #   other-frameSynchronous.txt
    #   other-volumeMetadataUtilities.txt
    with tempfile.TemporaryDirectory() as temp_dir:
        e = Experiment(data_folder)
        _ = e.flash_finder(
            output_folder=temp_dir,
            chunk_size=42,
        )

        # output files created
        assert os.path.exists(os.path.join(temp_dir, "hiResData.mat"))
        assert os.path.exists(os.path.join(temp_dir, "submissionParameters.txt"))
