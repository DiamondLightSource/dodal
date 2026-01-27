from ophyd_async.core import (
    StandardReadableFormat,
)
from ophyd_async.epics.adandor import Andor2DriverIO
from ophyd_async.epics.adcore import NDPluginBaseIO, SingleTriggerDetector
from ophyd_async.epics.core import epics_signal_r


class Andor2Point(SingleTriggerDetector):
    """Using the andor2 as if it is a massive point detector, read the read uncached
    value after a picture is taken."""

    def __init__(
        self,
        prefix: str,
        drv_suffix: str,
        read_uncached: dict[str, str],
        name: str = "",
        plugins: dict[str, NDPluginBaseIO] | None = None,
    ) -> None:
        """
        Parameters
        ----------
        prefix: str,
           Beamline camera pv
        drv_suffix : str,
            Camera pv suffix
        read_uncached: dict[str,str]
            A dictionary contains the name and the pv suffix for the statistic plugin.
        name: str:
            Name of the device.
        plugins:: Optional[dict[str, NDPluginBaseIO] | None
            Dictionary containing plugin that are forward to the base class.
        """
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            for k, v in read_uncached.items():
                setattr(self, k, epics_signal_r(float, prefix + v))

        super().__init__(
            drv=Andor2DriverIO(prefix + drv_suffix), name=name, plugins=plugins
        )
