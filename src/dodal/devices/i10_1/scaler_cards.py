from ophyd_async.core import StandardReadable

from dodal.devices.current_amplifiers import StruckScaler


class I10JScalerCard(StandardReadable):
    def __init__(self, prefix, name: str = "") -> None:
        with self.add_children_as_readables():
            self.mon = StruckScaler(prefix=prefix, suffix=".S17")
            self.tey = StruckScaler(prefix=prefix, suffix=".S18")
            self.fy = StruckScaler(prefix=prefix, suffix=".S19")
            self.fy2 = StruckScaler(prefix=prefix, suffix=".S20")
        super().__init__(name)
