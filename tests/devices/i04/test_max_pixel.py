import numpy as np
import pytest

from dodal.devices.i04.max_pixel import MaxPixel


@pytest.fixture
def mock_array():
    arr = [[0, 29, 60, 80], [100, 100, 110, 200], [100, 100, 110, 200], [0, 50, 50, 50]]


# test that the correct max is found
