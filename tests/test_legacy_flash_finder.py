import os.path
import tempfile
from wbi.legacy.flash_finder import flash_finder

data_folder = os.path.join(os.path.dirname(__file__), "test_data")


def test_flash_finder():
    # input_folder needs to have
    #   sCMOS_Frames_U16_1024x512.dat or frames_U16_1024x512.dat
    #   BFP.txt (optional)
    #   framesDetails.txt
    #   other-frameSynchronous.txt
    #   other-volumeMetadataUtilities.txt
    with tempfile.TemporaryDirectory() as temp_dir:
        _ = flash_finder(input_folder=data_folder, output_folder=temp_dir, chunksize=42)

        # output files created
        assert os.path.exists(os.path.join(temp_dir, "hiResData.mat"))
        assert os.path.exists(os.path.join(temp_dir, "CameraFrameData.txt"))
        assert os.path.exists(os.path.join(temp_dir, "submissionParameters.txt"))
