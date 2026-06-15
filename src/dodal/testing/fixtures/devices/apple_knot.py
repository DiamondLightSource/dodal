import pytest

from dodal.devices.beamlines.i05_shared import (
    APPLE_KNOT_EXCLUSION_ZONES,
)
from dodal.devices.insertion_device.apple_knot_controller import AppleKnotPathFinder


@pytest.fixture
def apple_knot_i05_path_finder() -> AppleKnotPathFinder:
    return AppleKnotPathFinder(APPLE_KNOT_EXCLUSION_ZONES)
