from typing import Annotated

from ophyd_async.core import SignalR, StandardReadable
from ophyd_async.core import StandardReadableFormat as Format


class BeamsizeBase(StandardReadable):
    x_um: Annotated[SignalR[float], Format.HINTED_SIGNAL]
    y_um: Annotated[SignalR[float], Format.HINTED_SIGNAL]
