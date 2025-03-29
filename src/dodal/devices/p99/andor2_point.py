from ophyd_async.epics.adandor import Andor2DriverIO
from ophyd_async.epics.adcore import SingleTriggerDetector
from ophyd_async.epics.core import epics_signal_r


class Andor2Point(SingleTriggerDetector):
    """Using the andor2 as if it is a massive point detector, read the meanValue after
    a picture is taken."""

    def __init__(
        self,
        prefix: str,
        name: str = "",
    ) -> None:
        self.mean = epics_signal_r(float, prefix + "-EA-DET-03:STAT:MeanValue_RBV")
        super().__init__(
            drv=Andor2DriverIO(prefix + "-EA-DET-03:CAM:"),
            read_uncached=[self.mean],
            name=name,
        )
