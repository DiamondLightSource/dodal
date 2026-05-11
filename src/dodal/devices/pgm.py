from ophyd_async.core import (
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
)
from ophyd_async.epics.core import epics_signal_rw
from ophyd_async.epics.motor import Motor


class PlaneGratingMonochromator(StandardReadable):
    """Plane grating monochromator, it is use in soft x-ray beamline to generate
    monochromic beam.

    Args:
        prefix (str): Beamline specific part of the PV.
        grating (type[StrictEnum]): The Enum for the grating table.
        grating_pv (str): The suffix PV part of grating PV.
        name (str, optional): Name of the device.
    """

    def __init__(
        self,
        prefix: str,
        grating: type[StrictEnum],
        grating_pv: str = "GRATINGSELECT:SELECT",
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.energy = Motor(prefix + "ENERGY")
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.grating = epics_signal_rw(grating, prefix + grating_pv)
            self.cff = epics_signal_rw(float, prefix + "CFF")

        super().__init__(name=name)
