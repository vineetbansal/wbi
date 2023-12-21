import os.path
import tempfile
from wbi.experiment import Experiment
from wbi.legacy.flash_finder import flash_finder


def test_flash_finder(data_folder):
    # input_folder needs to have
    #   sCMOS_Frames_U16_1024x512.dat or frames_U16_1024x512.dat
    #   BFP.txt (optional)
    #   framesDetails.txt
    #   other-frameSynchronous.txt
    #   other-volumeMetadataUtilities.txt
    with tempfile.TemporaryDirectory() as temp_dir:
        e = Experiment(data_folder)
        _ = flash_finder(
            input_folder=data_folder,
            experiment=e,
            output_folder=temp_dir,
            chunk_size=42,
        )

        # output files created
        assert os.path.exists(os.path.join(temp_dir, "hiResData.mat"))
        assert os.path.exists(os.path.join(temp_dir, "submissionParameters.txt"))
