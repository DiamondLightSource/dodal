from ophyd_async.core import StandardReadable, StandardReadableFormat
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class RGBDiodes(StandardReadable):
    """Red, green and blue diodes read through an Enz LoCuM4 current amplifier.

    The amplifier outputs are wired into the analogue inputs of a PandA. This device
    only provides the live values and the amplifier gain. The triggered min, max
    and mean values are captured by PCAP and written by the PandA device itself.

    Args:
        panda_prefix (str): Prefix of the PandA block the amplifier is wired into,
            the channel number is appended to this.
        amplifier_prefix (str): Prefix of the LoCuM4 amplifier.
        red_channel (int): PandA channel the red diode is wired into.
        green_channel (int): PandA channel the green diode is wired into.
        blue_channel (int): PandA channel the blue diode is wired into.
        name (str): Name of the device.

    Attributes:
        red (SignalR): The live amplified red diode signal, in raw counts.
        green (SignalR): The live amplified green diode signal, in raw counts.
        blue (SignalR): The live amplified blue diode signal, in raw counts.
        gain (SignalRW): The requested measuring range of the amplifier, e.g. "1uA"
            or "Auto", which is shared by all of its channels.
        gain_readback (SignalR): The measuring range the amplifier is actually on.
    """

    def __init__(
        self,
        panda_prefix: str,
        amplifier_prefix: str,
        red_channel: int = 5,
        green_channel: int = 6,
        blue_channel: int = 7,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.red = epics_signal_r(int, f"{panda_prefix}{red_channel}")
            self.green = epics_signal_r(int, f"{panda_prefix}{green_channel}")
            self.blue = epics_signal_r(int, f"{panda_prefix}{blue_channel}")
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            # Separate signals as the setpoint has an extra "Auto" choice
            self.gain = epics_signal_rw(str, f"{amplifier_prefix}SETRANGE")
            self.gain_readback = epics_signal_r(str, f"{amplifier_prefix}MRREADBACK")
        super().__init__(name=name)
