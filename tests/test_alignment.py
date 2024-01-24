from wbi.alignment import Alignment


def test_alignment(data_folder):
    alignment = Alignment(data_folder)
    assert len(alignment["lowResFluor2BF"]) == 4
    # TODO: rect1/rect2 are being stored in this key, but nowhere else
    assert len(alignment["S2AHiRes"]) == 6
    assert len(alignment["Hi2LowResF"]) == 4
    assert alignment["background"].shape == (1024, 512)
