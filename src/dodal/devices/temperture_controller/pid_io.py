from ophyd_async.core import Device, DeviceVector, StrictEnum
from ophyd_async.epics.core import epics_signal_rw


class Lakeshore336_PID_MODE(StrictEnum):
    OFF = "Off"
    CLOSED_LOOP_PID = "Closed Loop PID"
    ZONE = "Zone"
    OPEN_LOOP = "Open Loop"
    MONITOR_OUT = "Monitor Out"
    WARMUP_SUPPLY = "Warmup Supply"


class PID_INPUT_CHANNEL(StrictEnum):
    NONE = "None"
    INPUT_1 = "Input 1"
    INPUT_2 = "Input 2"
    INPUT_3 = "Input 3"
    INPUT_4 = "Input 4"


class PIDBaseIO(Device):
    def __init__(
        self,
        prefix: str,
        no_channels: int,
        mode_table: type[StrictEnum],
        input_channel_table: type[StrictEnum],
        name: str = "",
    ):
        """ """
        no_channels += 1
        self.p = DeviceVector(
            {
                i: epics_signal_rw(
                    float, write_pv=f"{prefix}P_S{i}", read_pv=f"{prefix}P{i}"
                )
                for i in range(1, no_channels)
            }
        )
        self.i = DeviceVector(
            {
                i: epics_signal_rw(
                    float, write_pv=f"{prefix}I_S{i}", read_pv=f"{prefix}I{i}"
                )
                for i in range(1, no_channels)
            }
        )
        self.d = DeviceVector(
            {
                i: epics_signal_rw(
                    float, write_pv=f"{prefix}D_S{i}", read_pv=f"{prefix}D{i}"
                )
                for i in range(1, no_channels)
            }
        )
        self.manual_output = DeviceVector(
            {
                i: epics_signal_rw(
                    float, write_pv=f"{prefix}MOUT_S{i}", read_pv=f"{prefix}MOUT{i}"
                )
                for i in range(1, no_channels)
            }
        )
        self.mode = DeviceVector(
            {
                i: epics_signal_rw(
                    mode_table,
                    write_pv=f"{prefix}OMMODE_S{i}",
                    read_pv=f"{prefix}OMMODE{i}",
                )
                for i in range(1, no_channels)
            }
        )
        self.input_channel = DeviceVector(
            {
                i: epics_signal_rw(
                    input_channel_table,
                    write_pv=f"{prefix}OMINPUT_S{i}",
                    read_pv=f"{prefix}OMINPUT{i}",
                )
                for i in range(1, no_channels)
            }
        )

        super().__init__(name=name)
