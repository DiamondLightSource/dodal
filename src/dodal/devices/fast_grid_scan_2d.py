import threading

from bluesky.plan_stubs import mv
from ophyd import (
    Component,
    Device,
    EpicsSignal,
    EpicsSignalRO,
    EpicsSignalWithRBV,
    Kind,
    Signal,
)
from ophyd.status import DeviceStatus, StatusBase

from dodal.devices.fast_grid_scan_common import GridScanCompleteStatus, GridScanParams
from dodal.devices.status import await_value


class FastGridScan2D(Device):
    x_steps: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "X_NUM_STEPS")
    y_steps: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "Y_NUM_STEPS")

    x_step_size: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "X_STEP_SIZE")
    y_step_size: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "Y_STEP_SIZE")

    dwell_time_ms: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "EXPOSURE_TIME")

    x_start: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "X_START")
    y1_start: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "Y_START")
    z1_start: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "Z_START")

    position_counter: EpicsSignal = Component(
        EpicsSignal, "POS_COUNTER_RBV", write_pv="POS_COUNTER"
    )
    x_counter: EpicsSignalRO = Component(EpicsSignalRO, "X_COUNTER")
    y_counter: EpicsSignalRO = Component(EpicsSignalRO, "Y_COUNTER")

    # note: 2d scans on VMXm don't currently have a 'scan invalid' indication
    # but this may be added in EPICS later. So fake one for now.
    scan_invalid: Signal = Component(Signal, kind=Kind.hinted, value=0)

    run_cmd: EpicsSignal = Component(EpicsSignal, "RUN.PROC")
    stop_cmd: EpicsSignal = Component(EpicsSignal, "STOP.PROC")
    status: EpicsSignalRO = Component(EpicsSignalRO, "SCAN_STATUS_RBV")

    expected_images: Signal = Component(Signal)

    # Kickoff timeout in seconds
    KICKOFF_TIMEOUT: float = 20.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def set_expected_images(*_, **__):
            x, y = self.x_steps.get(), self.y_steps.get()
            self.expected_images.put(x * y)

        self.x_steps.subscribe(set_expected_images)
        self.y_steps.subscribe(set_expected_images)

    def is_invalid(self) -> bool:
        if "GONP" in self.scan_invalid.pvname:
            return False
        return self.scan_invalid.get()

    def kickoff(self) -> StatusBase:
        # Check running already here?
        st = DeviceStatus(device=self, timeout=self.KICKOFF_TIMEOUT)

        def scan():
            try:
                self.run_cmd.put(1)
                await_value(self.status, 1).wait()
                st.set_finished()
            except Exception as e:
                st.set_exception(e)

        threading.Thread(target=scan, daemon=True).start()
        return st

    def complete(self) -> DeviceStatus:
        return GridScanCompleteStatus(self)

    def collect(self):
        return {}

    def describe_collect(self):
        return {}


def set_fast_grid_scan_params(scan: FastGridScan2D, params: GridScanParams):
    yield from mv(
        scan.x_steps,
        params.x_steps,
        scan.y_steps,
        params.y_steps,
        scan.x_step_size,
        params.x_step_size,
        scan.y_step_size,
        params.y_step_size,
        scan.dwell_time_ms,
        params.dwell_time_ms,
        scan.x_start,
        params.x_start,
        scan.y1_start,
        params.y1_start,
        scan.z1_start,
        params.z1_start,
        scan.position_counter,
        0,
    )
