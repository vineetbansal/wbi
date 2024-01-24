from wbi.alignment import Alignment


def test_alignment(data_folder):
    alignment = Alignment(data_folder)
    assert len(alignment["lowResFluor2BF"]) == 4
    assert len(alignment["S2AHiRes"]) == 6
    assert len(alignment["Hi2LowResF"]) == 4
    assert alignment["background"].shape == (1024, 512)
