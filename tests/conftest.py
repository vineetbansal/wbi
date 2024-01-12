import os.path
import pytest
from wbi.data.ondemand import CACHE_PATH


@pytest.fixture(scope="session")
def data_folder():
    return os.path.join(os.path.dirname(__file__), "test_data")


@pytest.fixture(scope="session")
def expensive_data_folder():
    return os.path.join(CACHE_PATH, "bs")
