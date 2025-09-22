from ophyd_async.core import Device, DeviceVector, SignalDatatypeT
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class LakeshoreControlChannel(Device):
    """
    Single control channel for a Lakeshore temperature controller.

    Provides access to setpoint, ramp rate, ramp enable, heater output, heater output range,
    PID parameters (P, I, D), and manual output for the channel.
    """

    def __init__(
        self,
        prefix: str,
        suffix: str,
        heater_type: type[SignalDatatypeT],
        name: str = "",
    ):
        """Initialize the LakeshoreControlChannel device.
        Parameters
        ----------
            prefix: str
                The EPICS prefix for the Lakeshore device.
            suffix: str
                Suffix for the channel, used to differentiate multiple channels.
            heater_type: SignalDatatypeT
                Type of the heater output range.
            name: str
                Optional name for the device.
        """

        def channel_rw(channel_type, pv_name):
            return epics_signal_rw(
                channel_type,
                f"{prefix}{pv_name}{suffix}",
                f"{prefix}{pv_name}_S{suffix}",
            )

        self.user_setpoint = channel_rw(channel_type=float, pv_name="SETP")
        self.ramp_rate = channel_rw(channel_type=float, pv_name="RAMP")
        self.ramp_enable = channel_rw(channel_type=int, pv_name="RAMPST")
        self.heater_output_range = channel_rw(channel_type=heater_type, pv_name="RANGE")
        self.p = channel_rw(channel_type=float, pv_name="P")
        self.i = channel_rw(channel_type=float, pv_name="I")
        self.d = channel_rw(channel_type=float, pv_name="D")
        self.manual_output = channel_rw(channel_type=float, pv_name="MOUT")
        self.heater_output = epics_signal_r(float, f"{prefix}{'HTR'}{suffix}")

        super().__init__(name=name)


class LakeshoreBaseIO(Device):
    """Base class for Lakeshore temperature controller IO.

    Provides access to control channels and readback channels for setpoint, ramp rate, heater output,
    and PID parameters. Supports both single and multiple control channel configurations.
    Note:
        Almost all models have a controller for each readback channel but some models
            only has a single controller for multiple readback channels.
    """

    def __init__(
        self,
        prefix: str,
        num_readback_channel: int,
        heater_setting: type[SignalDatatypeT],
        name: str = "",
        single_control_channel: bool = False,
    ):
        """Initialize the LakeshoreBaseIO device.

        Parameters
        -----------
            prefix: str
                The EPICS prefix for the Lakeshore device.
            num_readback_channel: int
                Number of readback channels to create.
            heater_setting: SignalDatatypeT
                Type of the heater setting.
            name: str
                Optional name for the device.
            single_control_channel: bool
                If True, use a single control channel for all readback.
        """

        suffixes = (
            [""]
            if single_control_channel
            else map(str, range(1, num_readback_channel + 1))
        )
        self.control_channels = DeviceVector(
            {
                i: LakeshoreControlChannel(
                    prefix=prefix, suffix=suffix, heater_type=heater_setting
                )
                for i, suffix in enumerate(suffixes, start=1)
            }
        )

        self.readback = DeviceVector(
            {
                i: epics_signal_r(
                    float,
                    read_pv=f"{prefix}KRDG{i - 1}",
                )
                for i in range(1, num_readback_channel + 1)
            }
        )
        super().__init__(
            name=name,
        )
