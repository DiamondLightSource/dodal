import threading

from bluesky.plan_stubs import mv
from ophyd import (
    Component,
    Device,
    EpicsSignal,
    EpicsSignalRO,
    EpicsSignalWithRBV,
    Signal,
)
from ophyd.status import DeviceStatus, StatusBase

from dodal.devices.fast_grid_scan import GridScanParamsCommon
from dodal.devices.status import await_value


class GridScanCompleteStatus(DeviceStatus):
    """
    A Status for the grid scan completion
    Progress bar functionality has been removed for now in the panda fast grid scan
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.device.status.subscribe(self._running_changed)

    def _running_changed(self, value=None, old_value=None, **kwargs):
        if (old_value == 1) and (value == 0):
            self.set_finished()
            self.clean_up()

    def clean_up(self):
        self.device.status.clear_sub(self._running_changed)


class PandAGridScanParams(GridScanParamsCommon):
    """
    Holder class for the parameters of a grid scan in a similar
    layout to EPICS. These params are used for the panda-triggered
    constant motion grid scan

    Motion program will do a grid in x-y then rotate omega +90 and perform
    a grid in x-z.

    The grid specified is where data is taken e.g. it can be assumed the first frame is
    at x_start, y1_start, z1_start and subsequent frames are N*step_size away.
    """

    run_up_distance_mm: float = 0.17


class PandAFastGridScan(Device):
    """This is similar to the regular FastGridScan device. It has two extra PVs: runup distance and time between x steps.
    Dwell time is not moved in this scan.
    """

    x_steps: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "X_NUM_STEPS")
    y_steps: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "Y_NUM_STEPS")
    z_steps: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "Z_NUM_STEPS")

    x_step_size: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "X_STEP_SIZE")
    y_step_size: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "Y_STEP_SIZE")
    z_step_size: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "Z_STEP_SIZE")

    # This value is fixed by the time between X steps detector deadtime. The only reason it is a PV
    # Is so the value can be read by the motion program in the PPMAC
    time_between_x_steps_ms = Component(EpicsSignalWithRBV, "TIME_BETWEEN_X_STEPS")

    run_up_distance: EpicsSignalWithRBV = Component(EpicsSignal, "RUNUP_DISTANCE")

    x_start: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "X_START")
    y1_start: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "Y_START")
    y2_start: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "Y2_START")
    z1_start: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "Z_START")
    z2_start: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "Z2_START")

    position_counter: EpicsSignalRO = Component(EpicsSignalRO, "Y_COUNTER")
    scan_invalid: EpicsSignalRO = Component(EpicsSignalRO, "SCAN_INVALID")

    run_cmd: EpicsSignal = Component(EpicsSignal, "RUN.PROC")
    stop_cmd: EpicsSignal = Component(EpicsSignal, "STOP.PROC")
    status: EpicsSignalRO = Component(EpicsSignalRO, "SCAN_STATUS")

    expected_images: Signal = Component(Signal)

    # Kickoff timeout in seconds
    KICKOFF_TIMEOUT: float = 5.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def set_expected_images(*_, **__):
            x, y, z = self.x_steps.get(), self.y_steps.get(), self.z_steps.get()
            first_grid = x * y
            second_grid = x * z
            self.expected_images.put(first_grid + second_grid)

        self.x_steps.subscribe(set_expected_images)
        self.y_steps.subscribe(set_expected_images)
        self.z_steps.subscribe(set_expected_images)

    def is_invalid(self) -> bool:
        if "GONP" in self.scan_invalid.pvname:
            return False
        return self.scan_invalid.get()

    def kickoff(self) -> StatusBase:
        # Check running already here?
        st = DeviceStatus(device=self, timeout=self.KICKOFF_TIMEOUT)

        def scan():
            try:
                self.log.debug("Running scan")
                self.run_cmd.put(1)
                self.log.debug("Waiting for scan to start")
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


def set_fast_grid_scan_params(scan: PandAFastGridScan, params: PandAGridScanParams):
    yield from mv(
        scan.x_steps,
        params.x_steps,
        scan.y_steps,
        params.y_steps,
        scan.z_steps,
        params.z_steps,
        scan.x_step_size,
        params.x_step_size,
        scan.y_step_size,
        params.y_step_size,
        scan.z_step_size,
        params.z_step_size,
        scan.x_start,
        params.x_start,
        scan.y1_start,
        params.y1_start,
        scan.y2_start,
        params.y2_start,
        scan.z1_start,
        params.z1_start,
        scan.z2_start,
        params.z2_start,
        scan.run_up_distance,
        params.run_up_distance_mm,
    )
