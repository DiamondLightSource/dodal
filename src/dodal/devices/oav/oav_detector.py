from enum import IntEnum

from ophyd import Component, Device, EpicsSignal


class ColorMode(IntEnum):
    """
    Enum to store the various color modes of the camera. We use RGB1.
    """

    MONO = 0
    BAYER = 1
    RGB1 = 2
    RGB2 = 3
    RGB3 = 4
    YUV444 = 5
    YUV422 = 6
    YUV421 = 7


class ZoomController(Device):
    """
    Device to control the zoom level, this is unfortunately on a different prefix
    from CAM.
    """

    percentage: EpicsSignal = Component(EpicsSignal, "ZOOMPOSCMD")

    # Level is the arbitrary level  that corresponds to a zoom percentage.
    # When a zoom is fed in from GDA this is the level it is refering to.
    level: EpicsSignal = Component(EpicsSignal, "MP:SELECT")

    zrst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.ZRST")
    onst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.ONST")
    twst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.TWST")
    thst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.THST")
    frst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.FRST")
    fvst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.FVST")

    @property
    def allowed_zoom_levels(self):
        return [
            self.zrst.get(),
            self.onst.get(),
            self.twst.get(),
            self.thst.get(),
            self.frst.get(),
            self.fvst.get(),
        ]


class EdgeOutputArrayImageType(IntEnum):
    """
    Enum to store the types of image to tweak the output array. We use Original.
    """

    ORIGINAL = 0
    GREYSCALE = 1
    PREPROCESSED = 2
    CANNY_EDGES = 3
    CLOSED_EDGES = 4
