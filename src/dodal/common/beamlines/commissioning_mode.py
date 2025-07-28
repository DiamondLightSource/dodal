"""Functions relating to commissioning mode.

Commissioning Mode can be enabled for a production beamline when there is no
beam. The intent is that when it is enabled, bluesky plans may be run without beam
and plans and devices will as far as is possible behave normally.
"""

from ophyd_async.core import SignalR

_commissioning_signal: SignalR | None = None


async def is_commissioning_mode_enabled() -> bool:
    """
    Determine whether commissioning mode is enabled.
    Returns:
        True if commissioning mode is enabled. False if commissioning mode
        is not enabled, or the commissioning signal has not been set."""
    return False


def set_commissioning_signal(signal: SignalR[bool]):
    """Commissioning mode is enabled by a PV which when set enables commissioning mode.
    This allows beamline staff to ensure that commissioning mode is disabled prior
    to production use, via their own 'good morning' startup scripts.
    Args:
        signal: The signal which will be read in order to determine whether
        commissioning mode is enabled."""
    pass
