from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class AutocollimatorAcquire(StrictEnum):
    DONE = "Done"
    ACQUIRE = "Acquire"


class Autocollimator(StandardReadable):
    """Device representing Autocollimator in Optical Metrology Lab

    Attributes:
        x_average: float readable average x value over two seconds
        y_average: float readable average y value over two seconds
        x_rms: float readable root mean sqaured x value over two seconds
        y_rms: float readable root mean squared y value over two seconds
        acquire: AutocollimatorAcquire RW to start/start/monitor acquisition"""

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.x_average = epics_signal_r(float, f"{prefix}X:AVG")

            self.y_average = epics_signal_r(float, f"{prefix}Y:AVG")

            self.x_rms = epics_signal_r(float, f"{prefix}X:RMS")
            self.y_rms = epics_signal_r(float, f"{prefix}Y:RMS")

        self.acquire = epics_signal_rw(AutocollimatorAcquire, f"{prefix}Acquire")

        super().__init__(name=name)
