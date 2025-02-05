from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class AutocollimatorAcquire(StrictEnum):
    DONE = "Done"
    ACQUIRE = "Acquire"


class Autocollimator(StandardReadable):
    """Device representing Autocollimator in Optical Metrology Lab"""

    def __init__(self, prefix: str):
        with self.add_children_as_readables():
            self.x_average = epics_signal_r(float, f"{prefix}X:AVG")

        self.y_average = epics_signal_r(float, f"{prefix}Y:AVG")

        self.x_rms = epics_signal_r(float, f"{prefix}X:RMS")
        self.y_rms = epics_signal_r(float, f"{prefix}Y:RMS")

        self.acquire = epics_signal_rw(AutocollimatorAcquire, f"{prefix}Acquire")
