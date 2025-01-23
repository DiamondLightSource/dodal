from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class S4SlitGaps(StandardReadable):
    """Note that the S4 slits have a different PV fromat to other beamline slits"""

    def __init__(self, prefix: str, name="") -> None:
        with self.add_children_as_readables():
            self.xgap = Motor(prefix + "XGAP")
            self.ygap = Motor(prefix + "YGAP")
            super().__init__(name=name)
