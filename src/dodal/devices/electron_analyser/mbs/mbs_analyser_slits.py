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
    P100_0_1_CURVED = "100 0.1 curved"
    P200_0_1_STRAIGHT = "200 0.1 straight"
    P300_0_2_CURVED = "300 0.2 curved"
    P400_0_2_STRAIGHT = "400 0.2 straight"
    P500_0_2_STRAIGHT = "500 0.2 straight"
    P600_0_3_STRAIGHT = "600 0.3 straight"
    P700_0_5_STRAIGHT = "700 0.5 straight"
    P800_0_8_STRAIGHT = "800 0.8 straight"
    P850_3_HOLE = "850 3 hole"
    P900_1_5_STRAIGHT = "900 1.5 straight"


class EntranceSlitInformation(BaseModel):
    direction: str = "vertical"
    setting: int = 100
    size: float = 0.1
    shape: str = "curved"

    @classmethod
    def from_slit_positions(cls, pos: SlitPosition):
        setting, size, shape = str(pos).split()
        return cls(setting=int(setting), size=float(size), shape=shape)

    def to_slit_position(self) -> SlitPosition:
        return SlitPosition(f"{self.setting} {self.size:g} {self.shape}")


class EntranceSlitInformationDevice(StandardReadable):
    """Device that connects to epics signal containing slit information from an enum
    value. This is synced with soft signals as individual signals which can be added as
    config_signals to give to detectors to save as nicely formatted data.
    """

    def __init__(self, pv: str, name: str = ""):
        self.slit_info = epics_signal_rw(SlitPosition, pv)
        # Formatted slit info as individual soft signals for metadata
        with self.add_children_as_readables():
            self.direction, self._direction_w = soft_signal_r_and_setter(str)
            self.setting, self._setting_w = soft_signal_r_and_setter(int)
            self.size, self._size_w = soft_signal_r_and_setter(float)
            self.shape, self._shape_w = soft_signal_r_and_setter(str)
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: SlitPosition):
        await self.slit_info.set(value)

    async def connect(
        self,
        mock: bool | DeviceMock = False,
        timeout: float = DEFAULT_TIMEOUT,
        force_reconnect: bool = False,
    ) -> None:
        await super().connect(mock, timeout, force_reconnect)

        def _sync_soft_signals_with_epics(
            value: dict[str, Reading[SlitPosition]],
        ) -> None:
            val = value[self.slit_info.name]["value"]
            new_slit_info = EntranceSlitInformation.from_slit_positions(val)
            self._direction_w(new_slit_info.direction)
            self._setting_w(new_slit_info.setting)
            self._size_w(new_slit_info.size)
            self._shape_w(new_slit_info.shape)

        self.slit_info.subscribe(_sync_soft_signals_with_epics)
