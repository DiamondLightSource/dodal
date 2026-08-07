from pydantic import (
    StrictFloat,
    validate_call,
)

from dodal.common.general_maths.absorbers import (
    FixedDepth,
)
from dodal.devices.beamlines.i19.access_controlled.attenuator_motor_squad import (
    AttenuatorMotorPositions,
    PermittedKeyStr,
)
from dodal.devices.beamlines.i19.transmission.tx_api_protocols import (
    Attenuator,
    DiscretePositionIndexReader,
    IndexedFilterSet,
)


class FilterWheel(Attenuator):
    @validate_call
    def __init__(
        self,
        *,
        recognised_filters: IndexedFilterSet,
        motor_key: PermittedKeyStr,
        index_reader: DiscretePositionIndexReader,
    ):
        self.name_of_motor: PermittedKeyStr = motor_key
        self.absorbing_filters: IndexedFilterSet = recognised_filters
        self.wheel_reader: DiscretePositionIndexReader = index_reader

    def _calculate_absorption(
        self,
        *,
        xray_energy_kev: StrictFloat,
        attenuator_positions: AttenuatorMotorPositions,
    ) -> float:
        """Estimates foil attenuation at x-ray energy assuming input wheel position is not OUT.

        Args:
            xray_energy_kev: The x-ray energy in kiloelectronvolts.
            attenuator_positions: Motor positions for the calculation.

        Returns:
            a calculated foil absorption.
        """
        _extracted_wheel_index = self._extract_position(
            attenuator_positions=attenuator_positions
        )
        _selected_filter: FixedDepth = self._filter_at(_extracted_wheel_index)
        return _selected_filter.calculate_absorption_bn(xray_energy_kev=xray_energy_kev)

    def _consistent_with_absorber_removed(self, *, wheel_index: int) -> bool:
        return self.absorbing_filters.are_absorbers_out_of_beam_at_index(wheel_index)

    def _extract_position(
        self, *, attenuator_positions: AttenuatorMotorPositions
    ) -> int:
        _motor_positions = attenuator_positions.validated_and_complete()
        return int(_motor_positions[self.name_of_motor])

    def _filter_at(self, wheel_index: int) -> FixedDepth:
        return self.absorbing_filters.filter_at(wheel_index)

    @validate_call
    def are_consistent_with_absorber_removed(
        self, *, attenuator_positions: AttenuatorMotorPositions
    ) -> bool:
        _extracted_wheel_index: int = self._extract_position(
            attenuator_positions=attenuator_positions
        )
        return self._consistent_with_absorber_removed(
            wheel_index=_extracted_wheel_index
        )

    def is_in_the_out_position(self) -> bool:
        """API of any Attenuator - asks if it has been removed from the x-ray beam.

        When this reports True, there is no need for any energy specific absorption calculations.
        """
        _motor_index = self.wheel_reader.read_motor_index()
        return self._consistent_with_absorber_removed(wheel_index=_motor_index)
