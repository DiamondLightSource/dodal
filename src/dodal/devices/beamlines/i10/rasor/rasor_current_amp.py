from ophyd_async.core import StandardReadable

from dodal.devices.current_amplifiers import SR570, FemtoDDPCA


class RasorFemto(StandardReadable):
    def __init__(self, prefix: str, suffix: str = "GAIN", name: str = ""):
        with self.add_children_as_readables():
            self.ca1 = FemtoDDPCA(prefix + "-01:", suffix=suffix)
            self.ca2 = FemtoDDPCA(prefix + "-02:", suffix=suffix)
            self.ca3 = FemtoDDPCA(prefix + "-03:", suffix=suffix)
        super().__init__(name)


class RasorSR570(StandardReadable):
    def __init__(self, prefix: str, suffix: str = "SENS:SEL", name: str = ""):
        with self.add_children_as_readables():
            self.ca1 = SR570(prefix + "-04:", suffix=suffix)
            self.ca2 = SR570(prefix + "-05:", suffix=suffix)
            self.ca3 = SR570(prefix + "-06:", suffix=suffix)
        super().__init__(name)
