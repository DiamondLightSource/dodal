from ophyd_async.core import Device, DeviceVector
from ophyd_async.epics.core import epics_signal_rw


class PIDBaseIO(Device):
    def __init__(self, prefix: str, no_channels: int, name: str = ""):
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

        super().__init__(name=name)
