from typing import Annotated as A

from ophyd_async.core import SignalR, StandardReadable
from ophyd_async.core import StandardReadableFormat as Format
from ophyd_async.epics.core import PvSuffix


class Autocollimator(StandardReadable):
    """Device representing Autocollimator in Optical Metrology Lab"""

    x_average: A[SignalR[float], PvSuffix("X:AVG"), Format.HINTED_SIGNAL]
    y_average: A[SignalR[float], PvSuffix("X:AVG")]

    x_rms: A[SignalR[float], PvSuffix("X:RMS")]
    y_rms: A[SignalR[float], PvSuffix("Y:RMS")]
