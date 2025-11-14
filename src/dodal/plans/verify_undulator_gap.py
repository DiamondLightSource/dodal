from typing import Protocol, runtime_checkable

from bluesky import plan_stubs as bps

from dodal.devices.common_dcm import DoubleCrystalMonochromatorBase
from dodal.devices.undulator import UndulatorInKeV


@runtime_checkable
class CheckUndulatorDevices(Protocol):
    undulator: UndulatorInKeV
    dcm: DoubleCrystalMonochromatorBase


def verify_undulator_gap(devices: CheckUndulatorDevices):
    """Verify Undulator gap is correct - it may not be after a beam dump"""

    energy_in_keV = yield from bps.rd(devices.dcm.energy_in_keV.user_readback)  # noqa: N806
    yield from bps.abs_set(devices.undulator, energy_in_keV, wait=True)
