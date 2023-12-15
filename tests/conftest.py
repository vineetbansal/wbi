import os.path
import pytest


@pytest.fixture(scope="session")
def data_folder():
    return os.path.join(os.path.dirname(__file__), "test_data")
