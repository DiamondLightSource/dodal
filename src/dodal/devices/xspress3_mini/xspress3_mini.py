from ophyd import Component, Device, EpicsSignal, EpicsSignalRO, EpicsSignalWithRBV

from dodal.devices.xspress3_mini.xspress3_mini_channel import Xspress3MiniChannel


class Xspress3Mini(Device):
    # Assume only one channel for now
    channel_1 = Component(Xspress3MiniChannel, "C1_")

    erase: EpicsSignal = Component(EpicsSignal, "ERASE")
    get_max_num_channels = Component(EpicsSignalRO, "MAX_NUM_CHANNELS_RBV")

    acquire: EpicsSignal = Component(EpicsSignal, "Acquire")

    get_roi_calc_mini: EpicsSignal = Component(EpicsSignal, "MCA1:Enable_RBV")

    NUMBER_ROIS_DEFAULT = 6

    trigger_mode_mini: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "TriggerMode")

    roi_start_x: EpicsSignal = Component(EpicsSignal, "ROISUM1:MinX")
    roi_size_x: EpicsSignal = Component(EpicsSignal, "ROISUM1:SizeX")
    acquire_time: EpicsSignal = Component(EpicsSignal, "AcquireTime")
