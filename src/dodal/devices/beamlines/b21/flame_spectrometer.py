from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw_rbv, epics_signal_x


class FlameSpectrometer(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        self.filepath = epics_signal_rw_rbv(str, f"pva://{prefix}:FilePath")
        self.filename = epics_signal_rw_rbv(str, f"pva://{prefix}:FileName")
        self.exposure_time = epics_signal_rw_rbv(
            float, f"pva://{prefix}:IntegrationTime"
        )
        self.capture = epics_signal_rw_rbv(bool, f"pva://{prefix}:Capture")
        self.single_trigger = epics_signal_x(f"pva://{prefix}:SingleScan")

        self.scan_in_progress = epics_signal_r(bool, f"pva://{prefix}:ScanInProgress")

        super().__init__(name)
