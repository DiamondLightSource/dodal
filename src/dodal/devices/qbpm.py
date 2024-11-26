from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_r


class QBPM(StandardReadable):
    """
    A beam position monitor that gives a position and intensity of the beam.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.intensity_uA = epics_signal_r(float, f"{prefix}INTEN")

        super().__init__(name)
