from typing import Self

from bluesky.protocols import Reading
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    DeviceMock,
    StandardReadable,
    StrictEnum,
    soft_signal_r_and_setter,
)
from ophyd_async.epics.core import epics_signal_rw
from pydantic import BaseModel


class SlitPosition(StrictEnum):
    S005_A05_STRAIGHT = "Straight, S0.05, A0.5"
    S010_A10_STRAIGHT = "Straight, S0.1, A1.0"
    S010_A13_STRAIGHT = "Straight, S0.1, A1.3"
    S010_A19_STRAIGHT = "Straight, S0.1, A1.9"
    S020_A10_STRAIGHT = "Straight, S0.2, A1.0"
    S020_A19_STRAIGHT = "Straight, S0.2, A1.9"
    S040_A19_STRAIGHT = "Straight, S0.4, A1.9"
    S320_A54_STRAIGHT = "Straight, S3.2, A5.4"
    S020_A10_CURVED = "Curved, S0.2, A1.0"


class EntranceSlitInformation(BaseModel):
    direction: str = "Vertical"
    shape: str = "Curved"
    size: float = 0.1
    aperture: float = 1.0

    @classmethod
    def from_slit_positions(cls, pos: SlitPosition) -> Self:
        shape, size, aperture = str(pos).split(", ")
        return cls(
            direction="Vertical",
            shape=shape,
            size=float(size.removeprefix("S")),
            aperture=float(aperture.removeprefix("A")),
        )

    def to_slit_position(self) -> SlitPosition:
        return SlitPosition(f"{self.shape}, S{self.size:g}, A{self.aperture:.1f}")


class EntranceSlitInformationDevice(StandardReadable):
    """Device that connects to epics signal containing slit information from an enum
    value. This is synced with soft signals as individual signals which can be added as
    config_signals to give to detectors to save as nicely formatted data.
    """

    def __init__(self, pv: str, name: str = ""):
        self.slit_pos = epics_signal_rw(SlitPosition, pv)
        # Formatted slit info as individual soft signals for metadata
        with self.add_children_as_readables():
            self.shape, self._shape_w = soft_signal_r_and_setter(str)
            self.aperture, self._aperture_w = soft_signal_r_and_setter(float)
            self.size, self._size_w = soft_signal_r_and_setter(float)
            self.direction, self._direction_w = soft_signal_r_and_setter(str)
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: SlitPosition):
        await self.slit_pos.set(value)

    def _sync_soft_signals_with_epics(
        self,
        value: dict[str, Reading[SlitPosition]],
    ) -> None:
        val = value[self.slit_pos.name]["value"]
        new_slit_info = EntranceSlitInformation.from_slit_positions(val)
        self._direction_w(new_slit_info.direction)
        self._aperture_w(new_slit_info.aperture)
        self._size_w(new_slit_info.size)
        self._shape_w(new_slit_info.shape)

    async def connect(
        self,
        mock: bool | DeviceMock = False,
        timeout: float = DEFAULT_TIMEOUT,
        force_reconnect: bool = False,
    ) -> None:
        await super().connect(mock, timeout, force_reconnect)
        # subscribe_reading listeners are stored in a set, so repeatedly subscribing
        # this bound method is harmless and does not create duplicate callbacks.
        self.slit_pos.subscribe_reading(self._sync_soft_signals_with_epics)
