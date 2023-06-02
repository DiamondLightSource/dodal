from enum import Enum

from ophyd import Component, Device, EpicsSignal, EpicsSignalRO

from dodal.devices.xspress3_mini.xspress3_mini_roi import Xspress3MiniROI


class TimeSeriesValues(Enum):  # assuming IOC version 3
    START_VALUE = "Acquire"
    STOP_VALUE = "Done"
    UPDATE_VALUE = ""


class Xspress3MiniChannel(Device):
    # Assume 6 ROI's per channel and one channel. This might need to be changed
    ROI_1: Xspress3MiniROI = Component(Xspress3MiniROI, "MCA_ROI1_")
    ROI_2: Xspress3MiniROI = Component(Xspress3MiniROI, "MCA_ROI2_")
    ROI_3: Xspress3MiniROI = Component(Xspress3MiniROI, "MCA_ROI3_")
    ROI_4: Xspress3MiniROI = Component(Xspress3MiniROI, "MCA_ROI4_")
    ROI_5: Xspress3MiniROI = Component(Xspress3MiniROI, "MCA_ROI5_")
    ROI_6: Xspress3MiniROI = Component(Xspress3MiniROI, "MCA_ROI6_")

    pv_sca5_update_mini: EpicsSignal = Component(EpicsSignal, "SCAS:TS:TSAcquire")

    pv_roi_size: EpicsSignal = Component(
        EpicsSignal, "SCA5_HLM"
    )  # Strange as it doesn't use roi variable, but this does happen in gda code.
    pv_roi_llm = Component(EpicsSignal, "SCA5_LLM")
    # GDA code seems dodgy for these two variables.

    pv_time: EpicsSignalRO = Component(EpicsSignalRO, f"SCAS:{1}:TSArrayValue")
    pv_reset_ticks: EpicsSignalRO = Component(EpicsSignalRO, f"SCAS:{2}:TSArrayValue")
    pv_reset_count: EpicsSignalRO = Component(EpicsSignalRO, f"SCAS:{3}:TSArrayValue")
    pv_all_event: EpicsSignalRO = Component(EpicsSignalRO, f"SCAS:{4}:TSArrayValue")
    pv_all_good: EpicsSignalRO = Component(EpicsSignalRO, f"SCAS:{5}:TSArrayValue")
    pv_pileup: EpicsSignalRO = Component(EpicsSignalRO, f"SCAS:{8}:TSArrayValue")

    pv_time_series_acquire: EpicsSignal = Component(EpicsSignal, "SCAS:TS:TSAcquire")
