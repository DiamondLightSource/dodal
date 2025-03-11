import numpy as np
from ophyd_async.core import (
    Array1D,
    DeviceVector,
    StandardReadable,
    soft_signal_r_and_setter,
)
from ophyd_async.epics.core import epics_signal_r
from ophyd_async.epics.motor import Motor

from dodal.common.crystal_metadata import (
    CrystalMetadata,
    MaterialsEnum,
    make_crystal_metadata_from_material,
)


class Crystal(StandardReadable): ...


class CrystalRoll(Crystal): ...


class DCMCrystalRollAndPitch(Crystal): ...


class DCM(StandardReadable):
    """
    Common device for the double crystal monochromator (DCM), used to select the energy of the beam.

    Write other stuff

    Offset ensures that the beam exits the DCM at the same point, regardless of energy.

    Use https://github.com/DiamondLightSource/dodal/issues/592#issuecomment-2244871217 !
    """

    def __init__(self, prefix: str, name: str, crystals: tuple[DCMCrystal]):
        self.crystals: DeviceVector[DCMCrystal] = DeviceVector(
            {i: crystals[i] for i in range(len(crystals))}
        )
