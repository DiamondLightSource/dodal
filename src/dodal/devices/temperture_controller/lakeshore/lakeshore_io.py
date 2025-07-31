from ophyd_async.core import Device, DeviceVector, SignalDatatypeT
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class LakeshoreControlChannel(Device):
    def __init__(
        self,
        prefix: str,
        suffix: str,
        heater_type: type[SignalDatatypeT],
        name: str = "",
    ):
        self.user_setpoint = epics_signal_rw(
            float, f"{prefix}SETP{suffix}", f"{prefix}SETP_S{suffix}"
        )
        self.ramp_rate = epics_signal_rw(
            float, f"{prefix}RAMP{suffix}", f"{prefix}RAMP_S{suffix}"
        )
        self.ramp_enable = epics_signal_rw(
            int, f"{prefix}RAMPST{suffix}", f"{prefix}RAMPST_S{suffix}"
        )
        self.heater_output = epics_signal_r(float, f"{prefix}HTR{suffix}")
        self.heater_output_range = epics_signal_rw(
            heater_type, f"{prefix}RANGE{suffix}", f"{prefix}RANGE_S{suffix}"
        )

        self.p = epics_signal_rw(
            float, read_pv=f"{prefix}P{suffix}", write_pv="{prefix}P_S{suffix}"
        )

        self.i = epics_signal_rw(
            float, read_pv=f"{prefix}I{suffix}", write_pv="{prefix}I_S{suffix}"
        )
        self.d = epics_signal_rw(
            float, read_pv=f"{prefix}D{suffix}", write_pv="{prefix}D_S{suffix}"
        )
        self.manual_output = epics_signal_rw(
            float, read_pv=f"{prefix}MOUT{suffix}", write_pv="{prefix}MOUT_S{suffix}"
        )

        super().__init__(name=name)


class LakeshoreBaseIO(Device):
    def __init__(
        self,
        prefix: str,
        no_channels: int,
        heater_setting: type[SignalDatatypeT],
        name: str = "",
        single_control_channel: bool = False,
    ):
        """Base class for Lakeshore IO including setpoint ramp_ramp and heater."""
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
                    for i in range(1, no_channels + 1)
                }
            )

        self.readBack_channel = DeviceVector(
            {
                i: epics_signal_r(
                    float,
                    read_pv=f"{prefix}KRDG{i - 1}",
                )
                for i in range(1, no_channels + 1)
            }
        )
        super().__init__(
            name=name,
        )
