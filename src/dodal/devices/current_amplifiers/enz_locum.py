from ophyd_async.core import StandardReadable, StandardReadableFormat, StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class EnzLocumRange(StrictEnum):
    """Measuring range setpoint, the full scale current of the amplifier."""

    RANGE_100PA = "100pA"
    RANGE_1NA = "1nA"
    RANGE_10NA = "10nA"
    RANGE_100NA = "100nA"
    RANGE_1UA = "1uA"
    RANGE_10UA = "10uA"
    RANGE_100UA = "100uA"
    RANGE_1MA = "1mA"
    AUTO = "Auto"


class EnzLocumRangeReadback(StrictEnum):
    """Measuring range the amplifier is actually on."""

    RANGE_100PA = "100pA"
    RANGE_1NA = "1nA"
    RANGE_10NA = "10nA"
    RANGE_100NA = "100nA"
    RANGE_1UA = "1uA"
    RANGE_10UA = "10uA"
    RANGE_100UA = "100uA"
    RANGE_1MA = "1mA"


class EnzLocumBiasSource(StrictEnum):
    """Bias voltage source setpoint."""

    PLUS = "Plus"
    MINUS = "Minus"
    EXTERNAL = "External"
    GROUND = "Ground"


class EnzLocumBiasSourceReadback(StrictEnum):
    """Bias voltage source the amplifier is actually using."""

    PLUS = "Plus"
    MINUS = "Minus"
    EXTERNAL = "External"
    GROUND = "Ground"
    ERROR = "Err"


class EnzLocumIntegrationWindow(StrictEnum):
    """Integration window of the amplifier."""

    WINDOW_4 = "4"
    WINDOW_8 = "8"
    WINDOW_16 = "16"
    WINDOW_32 = "32"
    WINDOW_64 = "64"


class EnzLocum(StandardReadable):
    """Enz Locum low current amplifier.

    Attributes:
        range (SignalRW): The requested measuring range, e.g. "1uA" or "Auto", which
            is shared by all of the amplifier's channels.
        range_readback (SignalR): The measuring range the amplifier is actually on.
        range_max (SignalR): The full scale current of the measuring range the
            amplifier is actually on, in amps. Use this to convert the outputs to a
            current.
        autorange (SignalR): Whether the amplifier is automatically ranging.
        bias_source (SignalRW): The requested bias voltage source.
        bias_source_readback (SignalR): The bias voltage source actually in use.
        integration_window (SignalRW): The requested integration window.
        integration_window_readback (SignalR): The integration window actually in
            use.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.range = epics_signal_rw(EnzLocumRange, f"{prefix}SETRANGE")
            self.range_readback = epics_signal_r(
                EnzLocumRangeReadback, f"{prefix}MRREADBACK"
            )
            self.range_max = epics_signal_r(float, f"{prefix}RANGEMAX")
            self.autorange = epics_signal_r(bool, f"{prefix}AUTO")
            self.bias_source = epics_signal_rw(EnzLocumBiasSource, f"{prefix}SETBIASV")
            self.bias_source_readback = epics_signal_r(
                EnzLocumBiasSourceReadback, f"{prefix}BIASV"
            )
            self.integration_window = epics_signal_rw(
                EnzLocumIntegrationWindow, f"{prefix}SETWINDOW"
            )
            self.integration_window_readback = epics_signal_r(
                EnzLocumIntegrationWindow, f"{prefix}WINDOW"
            )
        super().__init__(name=name)
