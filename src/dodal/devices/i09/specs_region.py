from dodal.devices.i09.base_region import AbstractBaseRegion


class SPECSRegion(AbstractBaseRegion):
    bindingEnergy: bool = False
    passEnergy: float = 1
    value: float = 1
    centreEnergy: float = 0
    psuMode: str = "1.5keV"
    acquisitionMode: str = ""
