from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class AutocollimatorAcquire(StrictEnum):
    DONE = "Done"
    ACQUIRE = "Acquire"


class Autocollimator(StandardReadable):
    """Device representing Autocollimator in Optical Metrology Lab

    Attributes:
        CentroidX_RBV: float readable average x value over two seconds
        CentroidY_RBV: float readable average y value over two seconds
        SigmaX_RBV: float readable root mean sqaured x value over two seconds
        SigmaY_RBV: float readable root mean squared y value over two seconds
        acquire: AutocollimatorAcquire RW to start/start/monitor acquisition"""

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            # Attributes renamed to be similar to beamline OAVs:
            self.CentroidX_RBV = epics_signal_r(float, f"{prefix}X:AVG")

            self.CentroidY_RBV = epics_signal_r(float, f"{prefix}Y:AVG")

            self.SigmaX_RBV = epics_signal_r(float, f"{prefix}X:RMS")
            self.SigmaY_RBV = epics_signal_r(float, f"{prefix}Y:RMS")

        self.acquire = epics_signal_rw(AutocollimatorAcquire, f"{prefix}Acquire")

        super().__init__(name=name)
