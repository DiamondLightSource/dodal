from ophyd_async.core import Device, SignalDatatypeT

from ..device_helper import create_r_device_vector, create_rw_device_vector


class LakeshoreTemperatureIO(Device):
    """.
    Base class for Lakeshore temperature readback IO. It provides readback signals for temperature channels.
    """

    def __init__(
        self,
        prefix: str,
        no_channels: int,
        name: str = "",
    ):
        self.user_readback = create_r_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            read_pv="KRDG",
            signal_type=float,
            pv_index_offset=-1,
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
        """Base class for Lakeshore IO including setpoint ramp_ramp and heater."""
        self.user_setpoint = create_rw_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            write_pv="SETP_S",
            read_pv="SETP",
            signal_type=float,
            no_pv_suffix_index=single_control_channel,
        )

        self.ramp_rate = create_rw_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            write_pv="RAMP_S",
            read_pv="RAMP",
            signal_type=float,
            no_pv_suffix_index=single_control_channel,
        )

        self.ramp_enable = create_rw_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            write_pv="RAMPST_S",
            read_pv="RAMPST",
            signal_type=int,
            no_pv_suffix_index=single_control_channel,
        )

        self.heater_output = create_r_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            read_pv="HTR",
            signal_type=float,
            no_pv_suffix_index=single_control_channel,
        )

        self.heater_output_range = create_rw_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            write_pv="RANGE_S",
            read_pv="RANGE",
            signal_type=heater_setting,
            no_pv_suffix_index=single_control_channel,
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
        """Basic pid and manual output signals for lakeshore channels"""

        self.p = create_rw_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            write_pv="P_S",
            read_pv="P",
            signal_type=float,
            no_pv_suffix_index=single_control_channel,
        )
        self.i = create_rw_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            write_pv="I_S",
            read_pv="I",
            signal_type=float,
            no_pv_suffix_index=single_control_channel,
        )
        self.d = create_rw_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            write_pv="D_S",
            read_pv="D",
            signal_type=float,
            no_pv_suffix_index=single_control_channel,
        )

        self.manual_output = create_rw_device_vector(
            prefix=prefix,
            no_channels=no_channels,
            write_pv="MOUT_S",
            read_pv="MOUT",
            signal_type=float,
            no_pv_suffix_index=single_control_channel,
        )

        super().__init__(name=name)
