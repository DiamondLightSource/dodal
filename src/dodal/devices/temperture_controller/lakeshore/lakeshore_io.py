from ophyd_async.core import Device, SignalDatatypeT, StrictEnum

from ..device_helper import create_r_device_vector, create_rw_device_vector


class LAKESHORE336_HEATER_SETTING(StrictEnum):
    OFF = "Off"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class LAKESHORE336_PID_MODE(StrictEnum):
    OFF = "Off"
    CLOSED_LOOP_PID = "Closed Loop PID"
    ZONE = "Zone"
    OPEN_LOOP = "Open Loop"
    MONITOR_OUT = "Monitor Out"
    WARMUP_SUPPLY = "Warmup Supply"


class LAKESHORE336_PID_INPUT_CHANNEL(StrictEnum):
    NONE = "None"
    INPUT_1 = "Input 1"
    INPUT_2 = "Input 2"
    INPUT_3 = "Input 3"
    INPUT_4 = "Input 4"


class LAKESHORE340_PID_INPUT_CHANNEL(StrictEnum):
    INPUT_1 = "Loop 1"
    INPUT_2 = "Loop 2"


class LakeshoreTemperatureIO(Device):
    """.
    Base class for Lakeshore temperature IO. It provides readback signals for temperature channels.
    """

    def __init__(
        self,
        prefix: str,
        no_channels: int,
        name: str = "",
    ):
        self.readback = create_r_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            read_pv="KRDG",
            signal_type=float,
            zero_pv_index=True,
        )
        super().__init__(name=name)


class LakeshoreBaseIO(LakeshoreTemperatureIO):
    def __init__(
        self,
        prefix: str,
        no_channels: int,
        heater_setting: type[SignalDatatypeT],
        name: str = "",
        single_control_channel: bool = False,
    ):
        self.setpoint = create_rw_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            write_pv="SETP_S",
            read_pv="SETP",
            signal_type=float,
            single_control_channel=single_control_channel,
        )

        self.ramp_rate = create_rw_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            write_pv="RAMP_S",
            read_pv="RAMP",
            signal_type=float,
            single_control_channel=single_control_channel,
        )

        self.ramp_enable = create_rw_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            write_pv="RAMPST_S",
            read_pv="RAMPST",
            signal_type=int,
            single_control_channel=single_control_channel,
        )

        self.heater_output = create_r_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            read_pv="HTR",
            signal_type=float,
            single_control_channel=single_control_channel,
        )

        self.heater_output_range = create_rw_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            write_pv="RANGE_S",
            read_pv="RANGE",
            signal_type=heater_setting,
            single_control_channel=single_control_channel,
        )

        super().__init__(
            prefix=prefix,
            no_channels=no_channels,
            name=name,
        )


class PIDBaseIO(Device):
    def __init__(
        self,
        prefix: str,
        no_channels: int,
        name: str = "",
        single_control_channel: bool = False,
    ):
        self.p = create_rw_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            write_pv="P_S",
            read_pv="P",
            signal_type=float,
            single_control_channel=single_control_channel,
        )
        self.i = create_rw_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            write_pv="I_S",
            read_pv="I",
            signal_type=float,
            single_control_channel=single_control_channel,
        )
        self.d = create_rw_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            write_pv="D_S",
            read_pv="D",
            signal_type=float,
            single_control_channel=single_control_channel,
        )

        self.manual_output = create_rw_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            write_pv="MOUT_S",
            read_pv="MOUT",
            signal_type=float,
            single_control_channel=single_control_channel,
        )

        super().__init__(name=name)
