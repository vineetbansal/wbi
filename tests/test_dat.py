import numpy as np
from wbi.dat import Dat


def test_dat_load(data_folder):
    dat = Dat(data_folder)
    chunk = dat.load(count=7)
    assert chunk.shape == (1024, 512, 7)
    assert chunk.dtype == "uint16"


def test_dat_load1(data_folder):
    dat = Dat(data_folder)
    data = dat.load(count=90)
    chunk = dat.load(count=9, offset=21)
    assert np.allclose(chunk, data[:, :, 21:30])


def test_dat_chunks(data_folder):
    dat = Dat(data_folder)
    chunk_size = np.random.randint(1, 20)

    for i, chunk in enumerate(dat.chunks(chunk_size=chunk_size), 1):
        if i * chunk_size <= dat.n_frames:
            expected_shape = (dat.rows * 2, dat.cols, chunk_size)
        else:
            remaining_frames = dat.n_frames % chunk_size
            expected_shape = (dat.rows * 2, dat.cols, remaining_frames or chunk_size)

        assert (
            chunk.shape == expected_shape
        ), f"Chunk {i} shape mismatch: expected {expected_shape}, got {chunk.shape}"
