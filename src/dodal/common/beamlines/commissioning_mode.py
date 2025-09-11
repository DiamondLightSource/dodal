"""Functions relating to commissioning mode.

Commissioning Mode can be enabled for a production beamline when there is no
beam. The intent is that when it is enabled, bluesky plans may be run without beam
and plans and devices will as far as is possible behave normally.
"""

import bluesky.plan_stubs as bps
from bluesky.utils import MsgGenerator
from ophyd_async.core import SignalR

_commissioning_signal: SignalR | None = None


def read_commissioning_mode() -> MsgGenerator[bool]:
    """Utility method for reading the commissioning mode state from the context
    of a bluesky plan, where a baton may or may not be present, or
    commissioning mode is provided by some other mechanism."""
    if _commissioning_signal:
        return (yield from bps.rd(_commissioning_signal))
    else:
        return False


def set_commissioning_signal(signal: SignalR[bool] | None):
    """Commissioning mode is enabled by a PV which when set enables commissioning mode.
    This allows beamline staff to ensure that commissioning mode is disabled prior
    to production use, via their own 'good morning' startup scripts.
    Args:
        signal: The signal which will be read in order to determine whether
        commissioning mode is enabled."""
    global _commissioning_signal
    _commissioning_signal = signal
