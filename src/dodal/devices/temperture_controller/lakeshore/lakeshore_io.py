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
        def channel_rw(channel_type, pv_name):
            return epics_signal_rw(
                channel_type,
                f"{prefix}{pv_name}{suffix}",
                f"{prefix}{pv_name}_S{suffix}",
            )

        self.user_setpoint = channel_rw(channel_type=float, pv_name="SETP")
        self.ramp_rate = channel_rw(channel_type=float, pv_name="RAMP")
        self.ramp_enable = channel_rw(channel_type=int, pv_name="RAMPST")
        self.heater_output = channel_rw(channel_type=float, pv_name="HTR")
        self.heater_output_range = channel_rw(channel_type=heater_type, pv_name="RANGE")
        self.p = channel_rw(float, "P")
        self.i = channel_rw(float, "I")
        self.d = channel_rw(float, "D")
        self.manual_output = channel_rw(float, "MOUT")

        super().__init__(name=name)


class LakeshoreBaseIO(Device):
    """Base class for Lakeshore temperature controller IO.

    Provides access to control channels and readback channels for setpoint, ramp rate, heater output,
    and PID parameters. Supports both single and multiple control channel configurations.
    Note:
        Almost all model has a controller for each readback channel but some model
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
        if single_control_channel:
            self.control_channels = DeviceVector(
                {
                    1: LakeshoreControlChannel(
                        prefix=prefix, suffix="", heater_type=heater_setting
                    )
                }
            )
        else:
            self.control_channels = DeviceVector(
                {
                    i: LakeshoreControlChannel(
                        prefix=prefix, suffix=str(i), heater_type=heater_setting
                    )
                    for i in range(1, num_readback_channel + 1)
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
