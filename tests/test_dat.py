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
