from ophyd_async.core import Device
from ophyd_async.core._device import DeviceConnector
from ophyd_async.epics.core import epics_signal_r
from ophyd_async.epics.motor import Motor

from dodal.devices.slits import MinimalSlits, Slits


class I10SlitsBlades(Slits):
    """Slits with extra control for each blade."""

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.ring_blade = Motor(prefix + "XRING")
            self.hall_blade = Motor(prefix + "XHALL")
            self.top_blade = Motor(prefix + "YPLUS")
            self.bot_blade = Motor(prefix + "YMINUS")

        super().__init__(
            prefix=prefix,
            x_gap="XSIZE",
            x_centre="XCENTRE",
            y_gap="YSIZE",
            y_centre="YCENTRE",
            name=name,
        )


class BladeDrainCurrents(Device):
    """ "The drain current measurements on each blade. The drain current are due to
    photoelectric effect (https://en.wikipedia.org/wiki/Photoelectric_effect).
    Note the readings are in voltage as it is the output of a current amplifier."""

    def __init__(
        self,
        prefix: str,
        suffix_ring_blade: str = "SIG1",
        suffix_hall_blade: str = "SIG2",
        suffix_top_blade: str = "SIG3",
        suffix_bot_blade: str = "SIG4",
        name: str = "",
        connector: DeviceConnector | None = None,
    ) -> None:
        self.ring_blade_current = epics_signal_r(
            float, read_pv=prefix + suffix_ring_blade
        )
        self.hall_blade_current = epics_signal_r(
            float, read_pv=prefix + suffix_hall_blade
        )
        self.top_blade_current = epics_signal_r(
            float, read_pv=prefix + suffix_top_blade
        )
        self.bot_blade_current = epics_signal_r(
            float, read_pv=prefix + suffix_bot_blade
        )

        super().__init__(name, connector)


class I10PrimarySlits(Slits):
    """First slits of the beamline with very high power load, they are two square water
    cooled blocks(aperture/aptr) that overlap to produce slit like behavior."""

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.x_aptr_1 = Motor(prefix + "APTR1:X")
            self.x_aptr_2 = Motor(prefix + "APTR2:X")
            self.y_aptr_1 = Motor(prefix + "APTR1:Y")
            self.y_aptr_1 = Motor(prefix + "APTR2:Y")
        super().__init__(
            prefix=prefix,
            x_gap="XSIZE",
            x_centre="XCENTRE",
            y_gap="YSIZE",
            y_centre="YCENTRE",
            name=name,
        )


class I10Slits(Device):
    """Collection of all the i10 slits before end station."""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.s1 = I10PrimarySlits(
            prefix=prefix + "01:",
        )
        self.s2 = I10SlitsBlades(
            prefix=prefix + "02:",
        )
        self.s3 = I10SlitsBlades(
            prefix=prefix + "03:",
        )
        self.s4 = MinimalSlits(
            prefix=prefix + "04:",
            x_gap="XSIZE",
            y_gap="YSIZE",
        )
        self.s5 = I10SlitsBlades(
            prefix=prefix + "05:",
        )
        self.s6 = I10SlitsBlades(
            prefix=prefix + "06:",
        )
        super().__init__(name=name)


class I10SlitsDrainCurrent(Device):
    """Collection of all the drain current from i10 slits."""

    def __init__(
        self, prefix: str, name: str = "", connector: DeviceConnector | None = None
    ) -> None:
        self.s2 = BladeDrainCurrents(
            prefix=prefix + "AL-SLITS-02:",
            suffix_ring_blade="XRING:I",
            suffix_hall_blade="XHALL:I",
            suffix_top_blade="YPLUS:I",
            suffix_bot_blade="YMINUS:I",
        )
        self.s3 = BladeDrainCurrents(prefix=prefix + "DI-IAMP-01:")
        self.s4 = BladeDrainCurrents(prefix=prefix + "DI-IAMP-02:")
        self.s5 = BladeDrainCurrents(prefix=prefix + "DI-IAMP-03:")
        self.s6 = BladeDrainCurrents(prefix=prefix + "DI-IAMP-04:")
        super().__init__(name, connector)
