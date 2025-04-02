import asyncio
from collections.abc import Mapping
from typing import Annotated as A

from bluesky.protocols import Movable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    DeviceVector,
    SignalR,
    SignalRW,
    SignalW,
    StandardReadable,
    StrictEnum,
    wait_for_value,
)
from ophyd_async.core import StandardReadableFormat as Format
from ophyd_async.epics.core import (
    EpicsDevice,
    PvSuffix,
    epics_signal_r,
    epics_signal_w,
    epics_signal_x,
)


class BimorphMirrorOnOff(StrictEnum):
    ON = "ON"
    OFF = "OFF"


class BimorphMirrorMode(StrictEnum):
    HI = "HI"
    NORMAL = "NORMAL"
    FAST = "FAST"


class BimorphMirrorStatus(StrictEnum):
    IDLE = "Idle"
    BUSY = "Busy"
    ERROR = "Error"


class BimorphMirrorChannel(StandardReadable, Movable[float], EpicsDevice):
    """Collection of PVs comprising a single bimorph channel.

    Attributes:
        target_voltage: Float RW_RBV for target voltage, which can be set using parent mirror's all target proc
        output_voltage: Float RW_RBV for current voltage on bimorph
        status: BimorphMirrorOnOff readable for ON/OFF status of channel
        shift: Float writeable shifting channel voltage
    """

    target_voltage: A[SignalRW[float], PvSuffix.rbv("VTRGT"), Format.CONFIG_SIGNAL]
    output_voltage: A[SignalRW[float], PvSuffix.rbv("VOUT"), Format.HINTED_SIGNAL]
    status: A[SignalR[BimorphMirrorOnOff], PvSuffix("STATUS"), Format.CONFIG_SIGNAL]
    shift: A[SignalW[float], PvSuffix("SHIFT")]

    @AsyncStatus.wrap
    async def set(self, value: float):
        """Sets channel's VOUT to given value.

        Args:
            value: float to set VOUT to
        """
        await self.output_voltage.set(value)


class BimorphMirror(StandardReadable, Movable[Mapping[int, float]]):
    """Class to represent CAENels Bimorph Mirrors.

    Attributes:
        channels: DeviceVector of BimorphMirrorChannel, indexed from 1, for each channel
        enabled: Writeable BimorphOnOff
        commit_target_voltages: Procable signal that writes values in each channel's VTRGT to VOUT
        status: Readable BimorphMirrorStatus Busy/Idle status
        err: Alarm status"""

    def __init__(self, prefix: str, number_of_channels: int, name=""):
        """
        Args:
            prefix: str PV prefix
            number_of_channels: int number of channels on bimorph mirror (can be zero)
            name: str name of device

        Raises:
            ValueError: number_of_channels is less than zero"""

        if number_of_channels < 0:
            raise ValueError(f"Number of channels is below zero: {number_of_channels}")

        with self.add_children_as_readables():
            self.channels = DeviceVector(
                {
                    i: BimorphMirrorChannel(f"{prefix}C{i}:")
                    for i in range(1, number_of_channels + 1)
                }
            )
        self.enabled = epics_signal_w(BimorphMirrorOnOff, f"{prefix}ONOFF")
        self.commit_target_voltages = epics_signal_x(f"{prefix}ALLTRGT.PROC")
        self.status = epics_signal_r(BimorphMirrorStatus, f"{prefix}STATUS")
        self.err = epics_signal_r(str, f"{prefix}ERR")
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: Mapping[int, float], tolerance: float = 0.0001) -> None:
        """Sets bimorph voltages in parrallel via target voltage and all proc.

        Args:
            value: Dict of channel numbers to target voltages

        Raises:
            ValueError: On set to non-existent channel"""

        if any(key not in self.channels for key in value):
            raise ValueError(
                f"Attempting to put to non-existent channels: {[key for key in value if (key not in self.channels)]}"
            )

        # Write target voltages:
        await asyncio.gather(
            *[
                self.channels[i].target_voltage.set(target, wait=True)
                for i, target in value.items()
            ]
        )

        # Trigger set target voltages:
        await self.commit_target_voltages.trigger()

        # Wait for values to propogate to voltage out rbv:
        await asyncio.gather(
            *[
                wait_for_value(
                    self.channels[i].output_voltage,
                    tolerance_func_builder(tolerance, target),
                    timeout=DEFAULT_TIMEOUT,
                )
                for i, target in value.items()
            ],
            wait_for_value(
                self.status, BimorphMirrorStatus.IDLE, timeout=DEFAULT_TIMEOUT
            ),
        )


def tolerance_func_builder(tolerance: float, target_value: float):
    def is_within_value(x):
        return abs(x - target_value) <= tolerance

    return is_within_value
