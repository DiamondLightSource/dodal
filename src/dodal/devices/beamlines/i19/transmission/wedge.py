from pydantic import (
    StrictFloat,
    validate_call,
)

from dodal.common.general_maths.absorber_geometry import (
    TaperedGeometryProvider,
    WedgeGeometry,
)
from dodal.common.general_maths.absorbers import (
    WedgeAbsorber,
)
from dodal.common.general_maths.material_absorption_maths import (
    AbsorptionSpectrumSegment,
    MaterialAbsorptionSpectrum,
)
from dodal.devices.beamlines.i19.access_controlled.attenuator_motor_squad import (
    AttenuatorMotorPositions,
)
from dodal.devices.beamlines.i19.transmission.specification_types import (
    WedgeAbsorberSpecification,
    WedgeMotorScaleSpecification,
)
from dodal.devices.beamlines.i19.transmission.tx_api_protocols import (
    Attenuator,
    ContinuousPositionReader,
)


class Wedge(Attenuator):
    @validate_call
    def __init__(
        self,
        *,
        absorber_spec: WedgeAbsorberSpecification,
        motor_coordinates: WedgeMotorScaleSpecification,
        motor_readout: ContinuousPositionReader,
    ):
        # build out Wedge implementation subcomponents from the specifications
        self.position_readout = motor_readout
        self.coordinates = absorber_spec.motor_coordinates
        self.absorber = absorber_spec.build_absorber()

    @validate_call
    def _calculate_absorption(
        self,
        *,
        xray_energy_kev: StrictFloat,
        attenuator_positions: AttenuatorMotorPositions,
    ) -> float:
        _raw_position_mm: StrictFloat = self._extract_position(
            attenuator_positions=attenuator_positions
        )
        return self.absorber.calculate_absorption_bn(
            xray_energy_kev=xray_energy_kev, motor_position_mm=_raw_position_mm
        )

    def _consistent_with_absorber_removed(
        self, *, motor_position_mm: StrictFloat
    ) -> bool:
        return self.coordinates.is_consistent_with_absorber_out(
            motor_position=motor_position_mm
        )

    def _extract_position(
        self, *, attenuator_positions: AttenuatorMotorPositions
    ) -> float:
        _motor_positions = attenuator_positions.validated_and_complete()
        return _motor_positions[self.coordinates.axis_label]

    @validate_call
    def are_consistent_with_absorber_removed(
        self, *, attenuator_positions: AttenuatorMotorPositions
    ) -> bool:
        _raw_position_mm: StrictFloat = self._extract_position(
            attenuator_positions=attenuator_positions
        )
        return self._consistent_with_absorber_removed(
            motor_position_mm=_raw_position_mm
        )

    def is_in_the_out_position(self) -> bool:
        _latest_position = self.position_readout.read_motor_position_mm()
        return self._consistent_with_absorber_removed(
            motor_position_mm=_latest_position
        )
