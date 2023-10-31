from wbi.api import hello


def test_wbi():
    assert hello() == "Hello WBI"
