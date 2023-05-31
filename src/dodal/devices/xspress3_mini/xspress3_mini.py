from ophyd import Component, Device, EpicsSignal, EpicsSignalRO

from dodal.devices.xspress3_mini.xspress3_mini_channel import Xspress3MiniChannel


class Xspress3Mini(Device):
    # Assume only one channel for now
    channel_1 = Component(Xspress3MiniChannel, "C1_")

    pv_erase: EpicsSignal = Component(EpicsSignal, "ERASE")
    pv_get_max_num_channels = Component(EpicsSignalRO, "MAX_NUM_CHANNELS_RBV")

    pv_acquire: EpicsSignal = (Component(EpicsSignal, "Acquire"),)

    pv_get_roi_calc_mini: EpicsSignal = Component(EpicsSignal, "MCA1:Enable_RBV")

    NUMBER_ROIS_DEFAULT = 6

    set_trigger_mode_mini: EpicsSignal = Component(EpicsSignal, "TriggerMode")

    pv_get_trig_mode_mini: EpicsSignalRO = Component(EpicsSignalRO, "TriggerMode_RBV")

    pv_roi_start_x: EpicsSignal = Component(EpicsSignal, "ROISUM1:MinX")
    pv_roi_size_x: EpicsSignal = Component(EpicsSignal, "ROISUM1:SizeX")
    pv_acquire_time: EpicsSignal = Component(EpicsSignal, "AcquireTime")
