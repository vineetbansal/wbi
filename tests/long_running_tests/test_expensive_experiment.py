import tempfile
import os.path
import pytest
from wbi.experiment import Experiment
from wbi.data.ondemand import get_file


@pytest.mark.expensive
def test_flash_finder():
    files = [
        "framesDetails.txt",
        "LowMagBrain20231024_153442",
        "other-frameSynchronous.txt",
        "other-volumeMetadataUtilities.txt",
        "sCMOS_Frames_U16_1024x512.dat",
    ]
    with tempfile.TemporaryDirectory() as temp_dir:
        data_folder = os.path.dirname(list(map(get_file, files))[0])
        e = Experiment(data_folder)
        mat_data = e.flash_finder(
            output_folder=temp_dir,
        )

        flash_time = list(
            [
                [index[0], mat_data["frameTime"][index][0][0]]
                for index in mat_data["flashLoc"]
            ]
        )
        assert flash_time == [
            [2487, 150.719],
            [2702, 151.796],
            [2910, 152.848],
            [55739, 418.586],
            [55962, 419.703],
            [56177, 420.79],
            [56238, 421.095],
        ]
