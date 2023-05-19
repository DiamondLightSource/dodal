from unittest.mock import MagicMock

import pytest
from ophyd.sim import make_fake_device
from ophyd.status import Status, StatusBase

from dodal.devices.aperturescatterguard import ApertureScatterguard, InvalidApertureMove


@pytest.fixture
def fake_aperture_scatterguard():
    FakeApertureScatterguard = make_fake_device(ApertureScatterguard)
    ap_sg: ApertureScatterguard = FakeApertureScatterguard(name="test_ap_sg")
    yield ap_sg


def test_aperture_scatterguard_throws_error_if_outside_tolerance(
    fake_aperture_scatterguard: ApertureScatterguard,
):
    fake_aperture_scatterguard.aperture.z.motor_resolution.sim_put(0.001)
    fake_aperture_scatterguard.aperture.z.user_setpoint.sim_put(1)
    fake_aperture_scatterguard.aperture.z.motor_done_move.sim_put(1)

    with pytest.raises(InvalidApertureMove):
        fake_aperture_scatterguard._safe_move_within_datacollection_range(
            0, 0, 1.1, 0, 0
        )


def test_aperture_scatterguard_returns_status_if_within_tolerance(
    fake_aperture_scatterguard: ApertureScatterguard,
):
    fake_aperture_scatterguard.aperture.z.motor_resolution.sim_put(0.001)
    fake_aperture_scatterguard.aperture.z.user_setpoint.sim_put(1)
    fake_aperture_scatterguard.aperture.z.motor_done_move.sim_put(1)

    mock_set = MagicMock(return_value=Status(done=True, success=True))

    fake_aperture_scatterguard.aperture.x.set = mock_set
    fake_aperture_scatterguard.aperture.y.set = mock_set
    fake_aperture_scatterguard.aperture.z.set = mock_set

    fake_aperture_scatterguard.scatterguard.x.set = mock_set
    fake_aperture_scatterguard.scatterguard.y.set = mock_set

    status = fake_aperture_scatterguard._safe_move_within_datacollection_range(
        0, 0, 1, 0, 0
    )
    assert isinstance(status, StatusBase)
