from ophyd_async.core import Device, DeviceVector, StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class Lakeshore336(StrictEnum):
    OFF = "Off"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class LakeshoreBaseIO(Device):
    def __init__(
        self,
        prefix: str,
        no_channels: int,
        heater_table: type[StrictEnum],
        name: str = "",
    ):
        no_channels += 1
        self.setpoint = DeviceVector(
            {
                i: epics_signal_rw(
                    float, write_pv=f"{prefix}SETP_S{i}", read_pv=f"{prefix}SETP{i}"
                )
                for i in range(1, no_channels)
            }
        )

        self.readback = DeviceVector(
            {
                i: epics_signal_r(float, f"{prefix}KRDG{i - 1}")
                for i in range(1, no_channels)
            }
        )

        self.ramp_rate = DeviceVector(
            {
                i: epics_signal_rw(
                    float, write_pv=f"{prefix}RAMP_S{i}", read_pv=f"{prefix}RAMP{i}"
                )
                for i in range(1, no_channels)
            }
        )

        self.ramp_enable = DeviceVector(
            {
                i: epics_signal_rw(
                    float, write_pv=f"{prefix}RAMPST_S{i}", read_pv=f"{prefix}RAMPST{i}"
                )
                for i in range(1, no_channels)
            }
        )
        self.heater_output = DeviceVector(
            {i: epics_signal_r(float, f"{prefix}HTR{i}") for i in range(1, no_channels)}
        )

        self.heater_output_range = DeviceVector(
            {
                i: epics_signal_rw(
                    heater_table,
                    write_pv=f"{prefix}RANGE_S{i}",
                    read_pv=f"{prefix}RANGE{i}",
                )
                for i in range(1, no_channels)
            }
        )
        super().__init__(name=name)
