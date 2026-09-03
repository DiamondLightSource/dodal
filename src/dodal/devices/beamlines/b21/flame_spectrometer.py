from bluesky.protocols import Stageable, Triggerable
from ophyd_async.core import AsyncStatus, StandardReadable, wait_for_value
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw_rbv, epics_signal_x


class FlameSpectrometer(StandardReadable, Stageable, Triggerable):
    def __init__(self, prefix: str, name: str = ""):
        self.filepath = epics_signal_rw_rbv(str, f"pva://{prefix}FilePath")
        self.filename = epics_signal_rw_rbv(str, f"pva://{prefix}FileName")
        self.exposure_time_ms = epics_signal_rw_rbv(
            int, f"pva://{prefix}Advanced:IntegrationTime"
        )
        self.capture = epics_signal_rw_rbv(bool, f"pva://{prefix}Capture")
        self.single_trigger = epics_signal_x(f"pva://{prefix}SingleScan")

        self.scan_in_progress = epics_signal_r(bool, f"pva://{prefix}ScanInProgress")

        super().__init__(name)

    @AsyncStatus.wrap
    async def stage(self):
        await self.capture.set(True)

    @AsyncStatus.wrap
    async def trigger(self):
        exposure_time = await self.exposure_time_ms.get_value()
        await self.single_trigger.trigger()
        await wait_for_value(
            self.scan_in_progress, False, timeout=exposure_time * 1000 + 2
        )

    @AsyncStatus.wrap
    async def unstage(self):
        await self.capture.set(False)
