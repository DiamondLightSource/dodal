import asyncio
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
    ON="ON"
    OFF="OFF"


class BimorphMirrorMode(StrictEnum):
    HI="HI"
    NORMAL="NORMAL"
    FAST="FAST"


class BimorphMirrorStatus(StrictEnum):
    IDLE = "Idle"
    BUSY = "Busy"
    ERROR = "Error"


class BimorphMirrorChannel(StandardReadable, EpicsDevice):
    """Collection of PVs comprising a single bimorph channel.

    Attributes:
        vtrgt: Float RW_RBV for target voltage, which can be set using parent mirror's all target proc
        vout: Float RW_RBV for current voltage on bimorph
        status: BimorphMirrorOnOff readable for ON/OFF status of channel
        shift: Float writeable shifting channel voltage
    """

    vtrgt: A[SignalRW[float], PvSuffix.rbv("VTRGT"), Format.HINTED_SIGNAL]
    vout: A[SignalRW[float], PvSuffix.rbv("VOUT"), Format.HINTED_SIGNAL]
    status: A[SignalR[BimorphMirrorOnOff], PvSuffix("STATUS"), Format.HINTED_SIGNAL]
    shift: A[SignalW[float], PvSuffix("STATUS")]


class BimorphMirror(StandardReadable, Movable):
    """Class to represent CAENels Bimorph Mirrors.

    Attributes:
        number_of_channels: Non-ophyd int holding number_of_channels passed into __init__
        channels: DeviceVector of BimorphMirrorChannel, indexed from 1, for each channel
        on_off: Writeable BimorphOnOff
        alltrgt_proc: Procable signal that writes values in each channel's VTRGT to VOUT
        status: Readable BimorphMirrorStatus Busy/Idle status
        err: Alarm status

    """

    def __init__(self, prefix: str, name="", number_of_channels: int = 0):
        self.number_of_channels = number_of_channels

        with self.add_children_as_readables():
            self.channels = DeviceVector(
                {
                    i: BimorphMirrorChannel(f"{prefix}C{i}:")
                    for i in range(1, number_of_channels + 1)
                }
            )
        self.on_off = epics_signal_w(BimorphMirrorOnOff, f"{prefix}ONOFF")
        self.alltrgt_proc = epics_signal_x(f"{prefix}ALLTRGT.PROC")
        self.status = epics_signal_r(BimorphMirrorStatus, f"{prefix}STATUS")
        self.err = epics_signal_r(str, f"{prefix}ERR")

        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: dict[int, float]):
        """Sets bimorph voltages in parrallel via target voltage and all proc.

        Args:
            value: Dict of channel numbers to target voltages"""
        for i in value.keys():
            assert self.channels.get(i) is not None

        await asyncio.gather(
            *[self.channels[i].vtrgt.set(target, wait=True) for i, target in value.items()]
        )

        await self.alltrgt_proc.trigger()

        await asyncio.gather(
            *[
                wait_for_value(self.channels[i].vout, target, timeout=DEFAULT_TIMEOUT)
                for i, target in value.items()
            ]
        )
