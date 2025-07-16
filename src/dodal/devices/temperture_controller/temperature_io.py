from ophyd_async.core import Device, SignalDatatypeT, StrictEnum

from .device_helper import create_r_device_vector, create_rw_device_vector


class Lakeshore336(StrictEnum):
    OFF = "Off"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


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
    ):
        self.setpoint = create_rw_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            write_pv="SETP_S",
            read_pv="SETP",
            signal_type=float,
        )

        self.ramp_rate = create_rw_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            write_pv="RAMP_S",
            read_pv="RAMP",
            signal_type=float,
        )

        self.ramp_enable = create_rw_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            write_pv="RAMPST_S",
            read_pv="RAMPST",
            signal_type=int,
        )

        self.heater_output = create_r_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            read_pv="HTR",
            signal_type=float,
        )

        self.heater_output_range = create_rw_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            write_pv="RANGE_S",
            read_pv="RANGE",
            signal_type=heater_setting,
        )

        super().__init__(
            prefix=prefix,
            no_channels=no_channels,
            name=name,
        )
