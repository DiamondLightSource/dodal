from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class PinHole(StandardReadable):
    "Two motors stage for rasor pinhole"

    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.x = Motor(prefix + "X")
            self.y = Motor(prefix + "Y")
        super().__init__(name=name)


class Diffractometer(StandardReadable):
    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.tth = Motor(prefix + "TWOTHETA")
            self.th = Motor(prefix + "THETA")
            self.chi = Motor(prefix + "CHI")
            self.chamber_x = Motor(prefix + "X")
            self.alpha = Motor(prefix + "ALPHA")
        super().__init__(name=name)


class DetSlits(StandardReadable):
    "Detector slits"

    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.upstream = Motor(prefix + "1:TRANS")
            self.downstream = Motor(prefix + "2:TRANS")
        super().__init__(name=name)


class PaStage(StandardReadable):
    "Rasor detector stage"

    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.ttp = Motor(prefix + "TWOTHETA")
            self.thp = Motor(prefix + "THETA")
            self.py = Motor(prefix + "Y")
            self.pz = Motor(prefix + "Z")
            self.eta = Motor(prefix + "ETA")
        super().__init__(name=name)
