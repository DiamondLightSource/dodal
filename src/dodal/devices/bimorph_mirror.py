import asyncio
from typing import Annotated as A

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    DeviceVector,
    SignalR,
    SignalRW,
    SignalW,
    StandardReadable,
    StrictEnum,
    set_and_wait_for_other_value,
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

DEFAULT_TIMEOUT = 60


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


class BimorphMirrorChannel(StandardReadable, EpicsDevice):
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


class BimorphMirror(StandardReadable, Movable[list[float]]):
    """Class to represent CAENels Bimorph Mirrors.

    Attributes:
        channels: DeviceVector of BimorphMirrorChannel, indexed from 1, for each channel
        enabled: Writeable BimorphOnOff
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
    async def set(self, value: list[float]) -> None:
        """Sets bimorph voltages in parallel via target voltage and all proc.

        Args:
            value: List of float target voltages

        Raises:
            ValueError: On set to non-existent channel"""

        if len(value) != len(self.channels):
            raise ValueError(
                f"Length of value input array does not match number of \
                             channels: {len(value)} and {len(self.channels)}"
            )

        # Write target voltages in serial
        # Voltages are written in serial as bimorph PSU cannot handle simultaneous sets
        for i, target in enumerate(value):
            await wait_for_value(
                self.status, BimorphMirrorStatus.IDLE, timeout=DEFAULT_TIMEOUT
            )
            await set_and_wait_for_other_value(
                self.channels[i + 1].target_voltage,
                target,
                self.status,
                BimorphMirrorStatus.BUSY,
            )

        # Trigger set target voltages:
        await wait_for_value(
            self.status, BimorphMirrorStatus.IDLE, timeout=DEFAULT_TIMEOUT
        )
        await self.commit_target_voltages.trigger()

        # Wait for values to propogate to voltage out rbv:
        await asyncio.gather(
            *[
                wait_for_value(
                    self.channels[i + 1].output_voltage,
                    target,
                    timeout=DEFAULT_TIMEOUT,
                )
                for i, target in enumerate(value)
            ],
            wait_for_value(
                self.status, BimorphMirrorStatus.IDLE, timeout=DEFAULT_TIMEOUT
            ),
        )
