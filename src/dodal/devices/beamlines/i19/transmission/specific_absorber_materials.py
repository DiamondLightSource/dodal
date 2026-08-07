from typing import Final

from dodal.common.general_maths.interval import ClosedInterval
from dodal.devices.beamlines.i19.transmission.specification_types import (
    AbsorptionSpectrumSpecification,
    CorrectedEnergyDependenceSpecification,
    EnergyDependenceSpecification,
)

# Specifications for Absorber Materials used in the I19 Attenuation System

# Aluminium Wedge ( Primary Wedge )

# First ( and so far only ) curve fitted to wedge aluminium is valid over this keV range
VALID_ENERGY_INTERVAL_ALUMINIUM_1A: Final = ClosedInterval(lower=5, upper=30)

# As used in the primary wedge
# Values to be confirmed by beamline scientists
CALCULATOR_SPECIFICATION_ALUMINIUM_1A: Final = EnergyDependenceSpecification(
    photon_absorption=6.4873e4,
    roll_off=-2.96,
    valid_energy_interval_kev=VALID_ENERGY_INTERVAL_ALUMINIUM_1A,
)

MATERIAL_ABSORPTION_SPECTRUM_ALUMINIUM_1: Final = AbsorptionSpectrumSpecification(
    material_model="Aluminium_1",
    spectral_segments=(CALCULATOR_SPECIFICATION_ALUMINIUM_1A,),
)

# Specifications for Alumium Foil Absorber Material

# First ( and so far only ) curve fitted to foil aluminium is valid over this keV range
VALID_ENERGY_INTERVAL_ALUMINIUM_2A: Final = ClosedInterval(lower=5, upper=30)

# As used in the aluminium foil
# Values to be confirmed by beamline scientists
CALCULATOR_SPECIFICATION_ALUMINIUM_2A: Final = EnergyDependenceSpecification(
    photon_absorption=6.4873e4,
    roll_off=-2.96,
    valid_energy_interval_kev=VALID_ENERGY_INTERVAL_ALUMINIUM_2A,
)

MATERIAL_ABSORPTION_SPECTRUM_ALUMINIUM_2: Final = AbsorptionSpectrumSpecification(
    material_model="Aluminium_2",
    spectral_segments=(CALCULATOR_SPECIFICATION_ALUMINIUM_2A,),
)

# Specifications for Gold Foil Absorber Material

# First curve fitted to gold is potentially valid over this keV range
VALID_ENERGY_INTERVAL_GOLD_1A: Final = ClosedInterval(lower=5, upper=11.5)

CALCULATOR_SPECIFICATION_GOLD_1A: Final = EnergyDependenceSpecification(
    photon_absorption=7.87191216e5,  # TODO confirm with the beamline scientists
    roll_off=-2.52962901,  # TODO confirm with the beamline scientists
    valid_energy_interval_kev=VALID_ENERGY_INTERVAL_GOLD_1A,
)

# Second curve fitted to gold is potentially valid over this keV range
VALID_ENERGY_INTERVAL_GOLD_1B: Final = ClosedInterval(lower=15, upper=30)

CALCULATOR_SPECIFICATION_GOLD_1B: Final = EnergyDependenceSpecification(
    photon_absorption=3.63187927e6,  # TODO confirm with the beamline scientists
    roll_off=-2.59815489,  # TODO confirm with the beamline scientists
    valid_energy_interval_kev=VALID_ENERGY_INTERVAL_GOLD_1B,
)

MATERIAL_ABSORPTION_SPECTRUM_GOLD_1: Final = AbsorptionSpectrumSpecification(
    material_model="Gold_1",
    spectral_segments=(
        CALCULATOR_SPECIFICATION_GOLD_1A,
        CALCULATOR_SPECIFICATION_GOLD_1B,
    ),
)

# Specifications for Iron Foil Absorber Material

# First ( and so far only ) curve fitted to iron is valid over this keV range
VALID_ENERGY_INTERVAL_IRON_1A: Final = ClosedInterval(lower=8, upper=30)

CALCULATOR_SPECIFICATION_IRON_1A: Final = EnergyDependenceSpecification(
    photon_absorption=1.034347e6,
    roll_off=-2.8655,
    valid_energy_interval_kev=VALID_ENERGY_INTERVAL_IRON_1A,
)

MATERIAL_ABSORPTION_SPECTRUM_IRON_1: Final = AbsorptionSpectrumSpecification(
    material_model="Iron_1", spectral_segments=(CALCULATOR_SPECIFICATION_IRON_1A,)
)

# Resin Wedge ( Secondary Wedge )

# First ( and so far only ) curve + residual correction fitted to secondary wedge
# is valid over this keV range
VALID_ENERGY_INTERVAL_RESIN_1A: Final = ClosedInterval(lower=5, upper=22)

CALCULATOR_SPECIFICATION_RESIN_1A: Final = CorrectedEnergyDependenceSpecification(
    photon_absorption=3.8141e3,
    polynomial_correction_coefficients=(
        50.9211,
        -23.6148,
        4.2138,
        -0.3814,
        1.867e-2,
        -4.709e-4,
        4.796e-6,
    ),
    roll_off=-2.81706,
    valid_energy_interval_kev=VALID_ENERGY_INTERVAL_RESIN_1A,
)

MATERIAL_ABSORPTION_SPECTRUM_RESIN_1: Final = AbsorptionSpectrumSpecification(
    material_model="Resin_1", spectral_segments=(CALCULATOR_SPECIFICATION_RESIN_1A,)
)
