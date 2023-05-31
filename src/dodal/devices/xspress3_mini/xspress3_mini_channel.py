from ophyd import Component, Device, EpicsSignal, EpicsSignalRO

from dodal.devices.xspress3_mini.xspress3_mini_roi import Xspress3MiniROI


class Xspress3MiniChannel(Device):
    # Assume 6 ROI's per channel and one channel. This might need to be changed
    ROI_1 = Component(Xspress3MiniROI, "MCA_ROI1_")
    ROI_2 = Component(Xspress3MiniROI, "MCA_ROI2_")
    ROI_3 = Component(Xspress3MiniROI, "MCA_ROI3_")
    ROI_4 = Component(Xspress3MiniROI, "MCA_ROI4_")
    ROI_5 = Component(Xspress3MiniROI, "MCA_ROI5_")
    ROI_6 = Component(Xspress3MiniROI, "MCA_ROI6_")

    pv_sca5_update_arrays_mini = Component(EpicsSignalRO, "SCAS:TS:TSAcquire")

    pv_roi_size = Component(
        EpicsSignal, "SCA5_HLM"
    )  # Strange as it doesn't use roi variable, but this does happen in gda code.
    pv_roi_llm = Component(EpicsSignal, "SCA5_LLM")
    # GDA code seems dodgy for these two variables.

    pv_time = Component(EpicsSignalRO, f"SCAS:{1}:TSArrayValue")
    pv_reset_ticks = Component(EpicsSignalRO, f"SCAS:{2}:TSArrayValue")
    pv_reset_count = Component(EpicsSignalRO, f"SCAS:{3}:TSArrayValue")
    pv_all_event = Component(EpicsSignalRO, f"SCAS:{4}:TSArrayValue")
    pv_all_good = Component(EpicsSignalRO, f"SCAS:{5}:TSArrayValue")
    pv_pileup = Component(EpicsSignalRO, f"SCAS:{8}:TSArrayValue")
