from typing import Annotated as A

from ophyd_async.core import (
    SignalRW,
    StandardReadable,
)
from ophyd_async.core import StandardReadableFormat as Format
from ophyd_async.epics.core import EpicsDevice, PvSuffix


class Baton(StandardReadable, EpicsDevice):
    requested_user: A[
        SignalRW[str], PvSuffix("REQUESTED_USER"), Format.HINTED_UNCACHED_SIGNAL
    ]
    current_user: A[
        SignalRW[str], PvSuffix("CURRENT_USER"), Format.HINTED_UNCACHED_SIGNAL
    ]
