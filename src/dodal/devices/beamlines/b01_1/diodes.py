from ophyd_async.core import StandardReadable, StandardReadableFormat
from ophyd_async.epics.core import epics_signal_r

from dodal.devices.current_amplifiers import EnzLocum


class RGBDiodes(StandardReadable):
    """Red, green and blue diodes read through an Enz Locum current amplifier.

    The amplifier outputs are wired into the analogue inputs of a PandA. This device
    only provides the live values and the amplifier settings. The triggered min, max
    and mean values are captured by PCAP and written by the PandA device itself.

    Attributes:
        red (SignalR): The live amplified red diode signal, in raw counts.
        green (SignalR): The live amplified green diode signal, in raw counts.
        blue (SignalR): The live amplified blue diode signal, in raw counts.
        amplifier (EnzLocum): The amplifier, whose settings, including the measuring
            range shared by all of the diodes, are part of the configuration.
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
        with self.add_children_as_readables():
            self.amplifier = EnzLocum(amplifier_prefix)
        super().__init__(name=name)
