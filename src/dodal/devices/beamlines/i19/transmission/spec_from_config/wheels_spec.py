from functools import cached_property

from pydantic import (
    BaseModel,
    ConfigDict,
    StrictInt,
    model_validator,
)

from dodal.devices.beamlines.i19.transmission.spec_from_config.foil_spec import FoilSpec
from dodal.devices.beamlines.i19.transmission.spec_from_config.name_validation import (
    WheelNameValidation,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.system_aspect_base_parser import (
    SystemAspectBaseParser,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.system_configuration import (
    SystemConfiguration,
)


class WheelSpec(BaseModel):
    """The specification for a wheel (as specified by configuration, typically **JSON**).

    Notes:
        - Each filter wheel has a motor to rotate the wheel into and out of the x-ray beam:

    Attributes:
        foils: Occupancy dict mapping slot numbers to foils.
        out: The slot number to use for removing all absorbers from the x-ray beam.
        permissions: Those slot numbers which are permitted to be in use.
    """

    foils: dict[str, FoilSpec]
    out: StrictInt
    permissions: list[StrictInt]

    # Base Model internal setting to make this class immutable
    model_config = ConfigDict(frozen=True, extra="forbid")

    @model_validator(mode="after")
    def validate_out_in_permissions(self) -> "WheelSpec":
        """Ensures the 'out' slot position is included in the 'permissions' list."""
        if self.out in self.permissions:
            return self
        _msg: str = f"The permitted wheel slot indices {self.permissions} must include the 'out' slot position ({self.out} - but do not!"
        raise ValueError(_msg)

    @cached_property
    def all_active_indices(self) -> list[int]:
        """Reports slot indices only for permitted, specified, wheel positions.

        In detail this set comprises,
            - the index of the OUT position ( which will, canonically, have to be an empty slot )
            - plus the intersection of
                -- slots with permission for present day use
                -- slots with a specified foil absorber.

        Note: You can have a foil defined without permission to use it.
        Therefore need to check both specified foils and permissions:
            Because permissions get edited more frequently than You want to type in foil specs.
        """
        return [p for p in self.permissions if p == self.out or str(p) in self.foils]


class WheelsConfig(SystemAspectBaseParser[WheelSpec]):
    """Maps from highest level configuration (JSON) dict to extract wheel specifications.

    Uses base class method **extract_specifications** and some pythonic type handling magic.

    See Also:
        Base of this parser class, namely **SystemAspectBaseParser**
    """

    def validate_key_name(self, *, key_name: str) -> None:
        WheelNameValidation.validate_wheel_name(wheel_name=key_name)

    @classmethod
    def extract_wheel_specifications(
        cls,
        *,
        system_configuration: SystemConfiguration,
        wheel_identifier: str,
    ) -> WheelSpec:
        """Extracts a specific wheels specification from configuration of the transmission system."""
        _wheels: dict[str, WheelSpec] = cls.get_aspect_specifications(
            system_configuration=system_configuration
        )
        return _wheels[wheel_identifier]
