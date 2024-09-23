from ophyd_async.core import DeviceVector, StandardReadable

from dodal.devices.slits import Slits


class SixSlits(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.slits: DeviceVector[Slits] = DeviceVector(
                {
                    i: Slits(prefix=prefix + f"-AL-SLITS-{i:02}", name=f"slits_{i}")
                    for i in range(1, 6)
                }
            )
        super().__init__(name)
