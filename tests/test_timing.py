from wbi.timing import Timing


def test_timing(data_folder):
    timing = Timing(data_folder)
    # How many different time 'chunks' does the timing info have?
    assert timing.n_chunks == 1
