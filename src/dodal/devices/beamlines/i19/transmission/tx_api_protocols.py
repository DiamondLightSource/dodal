from typing import Protocol

from pydantic import (
    StrictFloat,
    validate_call,
)

from dodal.common.general_maths.absorbers import (
    FixedDepth,
)
from dodal.common.general_maths.transmission_interconversion import (
    CANONICAL_NON_ABSORPTION,
)
from dodal.devices.beamlines.i19.access_controlled.attenuator_motor_squad import (
    AttenuatorMotorPositions,
)


class Attenuator(Protocol):
    def _calculate_absorption(
        self,
        *,
        xray_energy_kev: StrictFloat,
        attenuator_positions: AttenuatorMotorPositions,
    ) -> float:
        """API: Calculate attenuation contribution at x-ray energy & (not OUT) motor positions.

        This hypothetical estimator will decide which motors are relevant,
        and compound Attenuators are going to sum over the results from each element.

        Args:
            xray_energy_kev: Hypothetical x-ray energy in kiloelectronvolts.
            attenuator_positions: Hypothetical motor positions.

        Returns:
            calculated absorption for the hypothetical situation,
            should only be called if the motor positions are not OUT.
        """
        ...

    def are_consistent_with_absorber_removed(
        self, *, attenuator_positions: AttenuatorMotorPositions
    ) -> bool:
        """API: Indicates that the elements within the motor positions are consistent with this particular absorber device being in the OUT position.

        Arguments:
            attenuator_positions: A bunch of motor position values to work with: These would be expected to include the motor of this attenuator.

        Raises:
            KeyError is raised if the tag for the motor of this Attenuator is not included in the attenuator_positions argument,
            since no valid boolean can be determined.
        """
        ...

    @validate_call
    def calculate_attenuation_bn(
        self,
        *,
        xray_energy_kev: StrictFloat,
        attenuator_positions: AttenuatorMotorPositions,
    ) -> float:
        if self.are_consistent_with_absorber_removed(
            attenuator_positions=attenuator_positions
        ):
            return CANONICAL_NON_ABSORPTION
        else:
            return self._calculate_absorption(
                xray_energy_kev=xray_energy_kev,
                attenuator_positions=attenuator_positions,
            )

    def is_in_the_out_position(self) -> bool:
        """API: Reports if an attenuating contribution is excluded by the absorber being stowed in the OUT position.

        Canonically defined OUT positions are provided for all absorbers and compound sub-systems of absorbers.
        """
        ...


class ContinuousPositionReader(Protocol):
    def read_motor_position_mm(self) -> float: ...


class DiscretePositionIndexReader(Protocol):
    def read_motor_index(self) -> int: ...


class IndexedFilterSet(Protocol):
    def are_absorbers_out_of_beam_at_index(self, index: int) -> bool: ...

    def filter_at(self, index: int) -> FixedDepth: ...
