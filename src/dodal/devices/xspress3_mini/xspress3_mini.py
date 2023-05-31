from ophyd import Component, Device, EpicsSignal, EpicsSignalRO

from dodal.devices.xspress3_mini.xspress3_mini_channel import Xspress3MiniChannel


class Xspress3Mini(Device):
    # Assume only one channel for now
    channel_1 = Component(Xspress3MiniChannel, "C1_")

    pv_erase: EpicsSignal = Component(
        EpicsSignal, "ERASE"
    )  # doErase function sets this PV to 1, which does the erase, IntergerFromEnumPV
    pv_get_max_num_channels = Component(
        EpicsSignalRO, "MAX_NUM_CHANNELS_RBV"
    )  # Using get on this PV should give the max number of channels, ReadOnlyIntegerPV

    # total_time_pvs: list[Component] = [] #These are read only

    # # For each channel, there is a pvsSCA5UpdateArraysMini PV, and these are all set to 'acquire_state = done' upon startup
    # for i in pv_get_max_num_channels.get():
    #     pv_sca5_update_arrays_mini_list.append(
    #         Component(EpicsSignalRO, f"C{i}_SCAS:TS:TSAcquire")
    #     )  # EnumPV, with the enum having ACQUIRE_STATE set...
    #     # ...to done on startup

    # Instead of using this for loop, use other device Xspress3MiniChannel and instantiate one for each channel. Assume one channel

    pv_acquire: EpicsSignal = (
        Component(EpicsSignal, "Acquire"),
    )  # enumPV, his is set to acquire state = ACQUIRE on startup, this value is set with no wait

    pv_get_roi_calc_mini: EpicsSignal = Component(
        EpicsSignal, "MCA1:Enable_RBV"
    )  # only .get() is used on this

    NUMBER_ROIS_DEFAULT = 6  # This might need to be changed

    # one element for each channel

    # Get pv_roi_llm like : channel_1.cls.ROI_1.cls.pv_roi_llm

    # [roi][channel] , need PVs which return the number of rois and the number of detector channels, then fill this up
    # accordingly... Where roi has NUMBER_ROIS_DEFAULT values, and channel has pv_get_max_num_channels.get() values

    # for roi in range(NUMBER_ROIS_DEFAULT):
    #     for channel in range(pv_get_max_num_channels.get()):
    #         pv_roi_llm[roi][channel] = Component(
    #             EpicsSignal, f"C{channel}_MCA_ROI{roi}_LLM"
    #         )  # IntegerPV
    #         pv_roi_size[roi][channel] = Component(
    #             EpicsSignal,
    #             f"C{channel}_SCA5_HLM",  # Strange as it doesn't use roi variable, but this does happen in gda code
    #         )  # IntegerPV

    # Logic of this for loop is unrolled and within Xspress3MiniChannel.py

    set_trigger_mode_mini: EpicsSignal = Component(
        EpicsSignal, "TriggerMode"
    )  # enumPV, putwait is used on this within a set_trigger_mode function

    pv_get_trig_mode_mini: EpicsSignalRO = Component(
        EpicsSignalRO, "TriggerMode_RBV"
    )  # Only get is used on this

    # roi_llm and roi_size are then used to get the roi limits in a get_roi_limits function

    pv_roi_start_x: EpicsSignal = Component(EpicsSignal, "ROISUM1:MinX")
    pv_roi_size_x: EpicsSignal = Component(EpicsSignal, "ROISUM1:SizeX")

    # A function readout_scalar_values uses the following integer RO pvs arrays:
    # pv_time: list[EpicsSignalRO] = [None] * pv_get_max_num_channels.get()
    # pv_reset_ticks: list[EpicsSignalRO] = [None] * pv_get_max_num_channels.get()
    # pv_reset_count: list[EpicsSignalRO] = [None] * pv_get_max_num_channels.get()
    # pv_all_event: list[EpicsSignalRO] = [None] * pv_get_max_num_channels.get()
    # pv_all_good: list[EpicsSignalRO] = [None] * pv_get_max_num_channels.get()
    # pv_pileup: list[EpicsSignalRO] = [None] * pv_get_max_num_channels.get()
    # pv_total_time: list[EpicsSignalRO] = [None] * pv_get_max_num_channels.get()

    # The names for these variables depend on useTSarrayValueNames in EpicsXspress3ControllerPvProvider.java . Assuming useTSarrayValueNames = True:

    # might need to use SCA_TEMPLATE here instead
    # for channel in pv_get_max_num_channels.get():
    #     pv_time[channel] = Component(
    #         EpicsSignalRO, f"C{self.this_channel}_SCAS:{0}:TSArrayValue"
    #     )
    #     pv_reset_ticks[channel] = Component(
    #         EpicsSignalRO, f"C{self.this_channel}_SCAS:{1}:TSArrayValue"
    #     )
    #     pv_reset_count[channel] = Component(
    #         EpicsSignalRO, f"C{self.this_channel}_SCAS:{2}:TSArrayValue"
    #     )
    #     pv_all_event[channel] = Component(
    #         EpicsSignalRO, f"C{self.this_channel}_SCAS:{3}:TSArrayValue"
    #     )
    #     pv_all_good[channel] = Component(
    #         EpicsSignalRO, f"C{self.this_channel}_SCAS:{4}:TSArrayValue"
    #     )
    #     pv_pileup[channel] = Component(
    #         EpicsSignalRO, f"C{self.this_channel}_SCAS:{7}:TSArrayValue"
    #     )

    # The second digit here is the index of the ScarIndex Enum values

    pv_acquire_time: EpicsSignal = Component(EpicsSignal, "AcquireTime")  # PV<double>


my_det = Xspress3Mini(prefix="BL03I-EA-XSP3-01:", name="test_fluorence")
my_det.wait_for_connection()
