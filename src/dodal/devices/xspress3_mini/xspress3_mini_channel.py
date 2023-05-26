from ophyd import Component, Device, EpicsSignal, EpicsSignalRO

from dodal.devices.xspress3_mini.xspress3_mini_roi import Xspress3MiniROI


class Xspress3MiniChannel(Device):
    total_channels = 0

    ROI_1 = Component(Xspress3MiniROI, "_MCA_ROI1")

    def __init__(self):
        prefix = "-EA-XSP3-01"
        Xspress3MiniChannel.total_channels += 1
        self.this_channel = Xspress3MiniChannel.total_channels

        self.pv_sca5_update_arrays_mini = Component(
            EpicsSignalRO, f"{prefix}:C{self.this_channel}_SCAS:TS:TSAcquire"
        )

        # Assume 6 ROI's per channel, This might need to be changed

        ROI_2 = Xspress3MiniROI()
        ROI_3 = Xspress3MiniROI()
        ROI_4 = Xspress3MiniROI()
        ROI_5 = Xspress3MiniROI()
        ROI_6 = Xspress3MiniROI()

        # for roi in range(NUMBER_ROIS_DEFAULT):
        #     for channel in range(pv_get_max_num_channels.get()):
        #         pv_roi_llm[roi][channel] = Component(
        #             EpicsSignal, f"{prefix}:C{channel}_MCA_ROI{roi}_LLM"
        #         )  # IntegerPV
        #         pv_roi_size[roi][channel] = Component(
        #             EpicsSignal,
        #             f"{prefix}:C{channel}_SCA5_HLM",  # Strange as it doesn't use roi variable, but this does happen in gda code
        #         )  # IntegerPV

        self.pv_roi_llm = [
            Component(
                EpicsSignal,
                f"{prefix}:C{self.this_channel}_MCA_ROI{ROI_1.this_roi_number}_LLM",
            ),
            Component(
                EpicsSignal,
                f"{prefix}:C{self.this_channel}_MCA_ROI{ROI_2.this_roi_number}_LLM",
            ),
            Component(
                EpicsSignal,
                f"{prefix}:C{self.this_channel}_MCA_ROI{ROI_3.this_roi_number}_LLM",
            ),
            Component(
                EpicsSignal,
                f"{prefix}:C{self.this_channel}_MCA_ROI{ROI_4.this_roi_number}_LLM",
            ),
            Component(
                EpicsSignal,
                f"{prefix}:C{self.this_channel}_MCA_ROI{ROI_5.this_roi_number}_LLM",
            ),
            Component(
                EpicsSignal,
                f"{prefix}:C{self.this_channel}_MCA_ROI{ROI_6.this_roi_number}_LLM",
            ),
        ]
        # IntegerPV's

        self.pv_roi_size = [
            Component(
                EpicsSignal,
                f"{prefix}:C{self.this_channel}_SCA5_HLM",  # Strange as it doesn't use roi variable, but this does happen in gda code
            )
        ] * Xspress3MiniROI.total_rois  # IntegerPV

        self.pv_time = Component(
            EpicsSignalRO, f"{prefix}:C{self.this_channel}_SCAS:{0}:TSArrayValue"
        )
        self.pv_reset_ticks = Component(
            EpicsSignalRO, f"{prefix}:C{self.this_channel}_SCAS:{1}:TSArrayValue"
        )
        self.pv_reset_count = Component(
            EpicsSignalRO, f"{prefix}:C{self.this_channel}_SCAS:{2}:TSArrayValue"
        )
        self.pv_all_event = Component(
            EpicsSignalRO, f"{prefix}:C{self.this_channel}_SCAS:{3}:TSArrayValue"
        )
        self.pv_all_good = Component(
            EpicsSignalRO, f"{prefix}:C{self.this_channel}_SCAS:{4}:TSArrayValue"
        )
        self.pv_pileup = Component(
            EpicsSignalRO, f"{prefix}:C{self.this_channel}_SCAS:{7}:TSArrayValue"
        )
