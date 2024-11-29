import asyncio

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, DeviceVector, StandardReadable, StrictEnum, wait_for_value
from ophyd_async.core import StandardReadableFormat as Format
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw_rbv, epics_signal_x, epics_signal_w


class BimorphMirrorOnOff(StrictEnum):
    ON="ON"
    OFF="OFF"


class BimorphMirrorMode(StrictEnum):
    HI="HI"
    NORMAL="NORMAL"
    FAST="FAST"
    

class BimorphMirrorChannel(StandardReadable):
    """Collection of PVs comprising a single bimorph channel.
    
    Attributes:
        vtrgt: Float RW_RBV for target voltage, which can be set using parent mirror's all target proc 
        vout: Float RW_RBV for current voltage on bimorph
        status: String readable for ON/OFF status of channel
        shift: Float writeable shifting channel voltage
    """
    def __init__(self, prefix: str, name=""):
        with self.add_children_as_readables(Format.HINTED_SIGNAL):
            self.vtrgt = epics_signal_rw_rbv(float, f"{prefix}:VTRGT")
            self.vout = epics_signal_rw_rbv(float, f"{prefix}:VOUT")
            self.status = epics_signal_r(str, f"{prefix}:STATUS")
        
        self.shift = epics_signal_w(float, f"{prefix}:SHIFT")

        super().__init__(name=name)


class BimorphMirror(StandardReadable, Movable):
    """Class to represent CAENels Bimorph Mirrors.
    
    Attributes:
        number_of_channels: Non-ophyd int holding number_of_channels passed into __init__
        channel_list: DeviceVector of BimorphMirrorChannel, indexed from 1, for each channel
        on_off: Writeable BimorphOnOff
        alltrgt_proc: Procable signal that writes values in each channel's VTRGT to VOUT
        status: Readable str Busy/Idle status
        channels: Number of channels
        temps: Readable str board temperature
        err: Alarm status

    """
    def __init__(self, prefix: str, name="", number_of_channels: int = 0):
        self.number_of_channels = number_of_channels

        with self.add_children_as_readables():
            self.channel_list = DeviceVector(
                {
                    i: BimorphMirrorChannel(f"{prefix}:C{i}", f"channel{i}")
                    for i in range(1, number_of_channels + 1)
                }
            )
        self.on_off = epics_signal_w(BimorphMirrorOnOff, f"{prefix}:ONOFF")
        self.alltrgt_proc = epics_signal_x(f"{prefix}:ALLTRGT.PROC")
        self.status = epics_signal_r(str, f"{prefix}:STATUS")
        self.channels = epics_signal_r(float, f"{prefix}:CHANNELS")
        self.status = epics_signal_r(str, f"{prefix}:STATUS")
        self.temps = epics_signal_r(str, f"{prefix}:TEMPS")
        self.err = epics_signal_r(str, f"{prefix}:ERR")

        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: dict[int, float]):
        """Sets bimorph voltages in parrallel via target voltage and all proc.
        
        Args:
            value: Dict of channel numbers to target voltages"""
        for i in value.keys():
            assert self.channel_list.get(i) is not None

        await asyncio.gather(
            *[self.channel_list[i].vtrgt.set(target) for i, target in value.items()]
        )

        await asyncio.gather(
            *[
                wait_for_value(self.channel_list[i].vtrgt, target, None)
                for i, target in value.items()
            ]
        )

        await self.alltrgt_proc.trigger()

        await asyncio.gather(
            *[
                wait_for_value(self.channel_list[i].vout, target, None)
                for i, target in value.items()
            ]
        )
