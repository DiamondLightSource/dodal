# Silicon D-spacing
import math
from math import asin
from scipy.constants import physical_constants

# This value taken from BeamLineEnergy_DCM_Angstrom_To_Deg_converter.xml
SI_111_SPACING_ANGSTROMS = 3.13475


def energy_to_wavelength(energy_kev: float) -> float:
    """Compute the wavelength in Angstroms
    Args:
        energy_kev:  The energy in keV
    Returns:
        The wavelength in Angstroms
    """
    return 1e7 / (energy_kev * physical_constants["electron volt-inverse meter relationship"][0])


def energy_to_bragg_angle(energy_kev: float) -> float:
    """Compute the bragg angle given the energy in kev.

    Args:
        energy_kev:  The energy in keV

    Returns:
        The bragg angle in degrees
    """
    wavelength_a = energy_to_wavelength(energy_kev)
    d = SI_111_SPACING_ANGSTROMS
    return asin(wavelength_a / (2 * d)) * 180 / math.pi

