from pydantic import (
    BaseModel,
    ConfigDict,
)

from dodal.devices.beamlines.i19.transmission.spec_from_config.lateral_motor_spec import (
    LateralMotorsConfig,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.material_absorption_spectrum_spec import (
    MaterialAbsorptionSpectralConfig,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.wedges_spec import (
    WedgesConfig,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.wheels_spec import (
    WheelsConfig,
)


class TransmissionSystemSpec(BaseModel):
    """Maps input configuration (i.e. JSON ) to highest level dict for I19 transmission system.

    Note:
         Sub-dictionaries carry the details of each aspect of the system.

    Attributes:
        lateral_motors: Position (scale) for wedge motors.
        materials: Absorption spectra for all absorber filter materials in wedges or foils.
        wedges: The shape, motor and material details for all system variable depth wedge absorbers.
        wheels: The slot occupancy, foil materials, motor name for all system filter wheels.
        usage_priority: Beamline scientists policy on which absorbers to prefer using first.
    """

    lateral_motors: LateralMotorsConfig
    materials: MaterialAbsorptionSpectralConfig
    wedges: WedgesConfig
    wheels: WheelsConfig

    # Base Model internal setting to make this class immutable and valid
    model_config = ConfigDict(frozen=True, extra="forbid")
