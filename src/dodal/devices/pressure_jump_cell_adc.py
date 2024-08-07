from enum import Enum
from functools import partial

from ophyd_async.core import (
    ConfigSignal,
    DeviceVector,
    SignalR,
    StandardReadable,
)
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw

from ophyd import ADComponent as ADC
from ophyd import (
    AreaDetector,
    CamBase,
    Component,
    Device,
    EpicsSignal,
    HDF5Plugin,
    OverlayPlugin,
    ProcessPlugin,
    ROIPlugin,
    StatsPlugin,
    Signal,
    StatusBase,
)

class PressureJumpAdcConfigParams:
    pass

class PressureJumpCellADC(AreaDetector):
    """
    High pressure X-ray cell fast ADC, used to capture pressure jumps.
    """
    cam = ADC(CamBase, "-EA-HPXC-01:CAM:")
    scale = ADC(ROIPlugin, "-EA-HPXC-01:SCALE:")
    # trig = # TODO support module adUtil NDPluginReframe? 
    # arr = # TODO support module ADCore NDPluginStdArrays? required?
    hdf5 = ADC(HDF5Plugin, "-DI-OAV-01:HDF5:")

    p1Roi = ADC(ROIPlugin, "-EA-HPXC-01:ROIP1:")
    p1Proc = ADC(ProcessPlugin, "-EA-HPXC-01:PROCP1:")
    p1Stats = ADC(StatsPlugin, "-EA-HPXC-01:STATP1:")

    p2Roi = ADC(ROIPlugin, "-EA-HPXC-01:ROIP2:")
    p2Proc = ADC(ProcessPlugin, "-EA-HPXC-01:PROCP2:")
    p2Stats = ADC(StatsPlugin, "-EA-HPXC-01:STATP2:")

    p3Roi = ADC(ROIPlugin, "-EA-HPXC-01:ROIP3:")
    p3Proc = ADC(ProcessPlugin, "-EA-HPXC-01:PROCP3:")
    p3Stats = ADC(StatsPlugin, "-EA-HPXC-01:STATP3:")

    def __init__(self, *args, params: PressureJumpAdcConfigParams, **kwargs):
        super().__init__(*args, **kwargs)
        self.parameters = params
        self.snapshot.oav_params = params
        self.subscription_id = None
        self._snapshot_trigger_subscription_id = None

    def wait_for_connection(self, all_signals=False, timeout=2):
        connected = super().wait_for_connection(all_signals, timeout)
        return connected

