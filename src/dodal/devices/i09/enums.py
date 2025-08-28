from ophyd_async.core import StrictEnum


class Grating(StrictEnum):
    """
    Enumeration of available grating types for the I09 device.

    Attributes:
        G_300: Grating with 300 lines per millimeter.
        G_400: Grating with 400 lines per millimeter.
        G_800: Grating with 800 lines per millimeter.
    """

    G_300 = "300 lines/mm"
    G_400 = "400 lines/mm"
    G_800 = "800 lines/mm"


class LensMode(StrictEnum):
    """
    Enumeration of available lens modes for the I09 device.

    Attributes:
        TRANSMISSION: Lens is set to transmission mode.
        ANGULAR45: Lens is set to 45-degree angular mode.
        ANGULAR60: Lens is set to 60-degree angular mode.
        ANGULAR56: Lens is set to 56-degree angular mode.
        ANGULAR45VUV: Lens is set to 45-degree angular mode for VUV (Vacuum Ultraviolet) applications.
    """

    TRANSMISSION = "Transmission"
    ANGULAR45 = "Angular45"
    ANGULAR60 = "Angular60"
    ANGULAR56 = "Angular56"
    ANGULAR45VUV = "Angular45VUV"


class PsuMode(StrictEnum):
    """
    Enumeration representing the available power supply unit (PSU) modes.

    Attributes:
        HIGH: Represents the high power mode.
        LOW: Represents the low power mode.
    """

    HIGH = "High"
    LOW = "Low"


class PassEnergy(StrictEnum):
    """
    Enumeration of possible pass energy values for the I09 device.

    Each member represents a specific pass energy setting, typically used in electron analyzers
    to control the energy resolution and transmission. The values are given as strings
    corresponding to their numeric values in electron volts (eV).

    Attributes:
        E5: Pass energy of 5 eV.
        E10: Pass energy of 10 eV.
        E20: Pass energy of 20 eV.
        E50: Pass energy of 50 eV.
        E70: Pass energy of 70 eV.
        E100: Pass energy of 100 eV.
        E200: Pass energy of 200 eV.
        E500: Pass energy of 500 eV.
    """

    E5 = "5"
    E10 = "10"
    E20 = "20"
    E50 = "50"
    E70 = "70"
    E100 = "100"
    E200 = "200"
    E500 = "500"
