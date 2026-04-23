from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_rw

from dodal.common.enums import OnOffUpper


class LEDLight(StandardReadable):
    """LED with brightness intensity and switch on/off control."""

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.intensity = epics_signal_rw(float, prefix + "PWMDEMAND")
            self.switch = epics_signal_rw(OnOffUpper, prefix + "TOGGLE")

        super().__init__(name)
