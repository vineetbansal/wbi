import os.path
import pytest
from wbi.data.ondemand import get_file


@pytest.fixture(scope="session")
def data_folder():
    return os.path.join(os.path.dirname(__file__), "test_data")


@pytest.fixture(scope="session")
def expensive_data_folder():
    files = [
        "bs/sCMOS_Frames_U16_1024x512.dat",
        "bs/framesDetails.txt",
        "bs/other-frameSynchronous.txt",
        "bs/other-volumeMetadataUtilities.txt",
        "bs/LowMagBrain20231024_153442",
    ]
    data_folder = os.path.dirname(list(map(get_file, files))[0])
    return data_folder
