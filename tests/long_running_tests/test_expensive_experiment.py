import tempfile
import pytest
from wbi.experiment import Experiment


@pytest.mark.expensive
def test_flash_finder(expensive_data_folder):
    with tempfile.TemporaryDirectory() as temp_dir:
        e = Experiment(expensive_data_folder)
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
