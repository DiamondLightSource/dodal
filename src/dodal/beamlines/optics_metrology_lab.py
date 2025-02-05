from pathlib import Path

from ophyd_async.core import StandardReadable, soft_signal_rw
from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import LocalDirectoryServiceClient, StaticVisitPathProvider
from dodal.devices.bimorph_mirror import BimorphMirror
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix

BL = "oml"
PREFIX = BeamlinePrefix("P32")

set_log_beamline(BL)
set_utils_beamline(BL)

set_path_provider(
    StaticVisitPathProvider(
        BL,
        Path("/tmp"),
        client=LocalDirectoryServiceClient(),
    )
)


@device_factory()
def mirror_one() -> BimorphMirror:
    return BimorphMirror(
        prefix=f"{PREFIX.beamline_prefix}-EA-IOC-09:G0:",
        number_of_channels=8,
        name="group_mirror_one",
    )


@device_factory()
def mirror_two() -> BimorphMirror:
    return BimorphMirror(
        prefix=f"{PREFIX.beamline_prefix}-EA-IOC-09:G1:",
        number_of_channels=8,
        name="group_mirror_two",
    )


class FakeSlits(StandardReadable):
    """Slits equivalent with fake x_gap, y_gap, y_centre"""

    def __init__(
        self,
        prefix: str,
        x_gap: str = "X:SIZE",
        y_gap: str = "Y:SIZE",
        x_centre: str = "X",
        y_centre: str = "Y:CENTRE",
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.x_centre = Motor(prefix + x_centre)

            self.y_centre = soft_signal_rw(float)
            self.x_gap = soft_signal_rw(float)
            self.y_gap = soft_signal_rw(float)
        super().__init__(name=name)


@device_factory()
def slits() -> FakeSlits:
    return FakeSlits(prefix=f"{PREFIX.beamline_prefix}-MO-NOM-01:", name="slits")
