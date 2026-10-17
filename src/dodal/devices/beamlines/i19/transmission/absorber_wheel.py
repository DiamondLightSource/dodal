from typing import Final, Protocol

from dodal.common.general_maths.absorber_geometry import FoilGeometry
from dodal.common.general_maths.absorbers import FixedDepth, FoilAbsorber
from dodal.common.general_maths.transmission_interconversion import (
    CANONICAL_NON_ABSORPTION,
)
from dodal.devices.beamlines.i19.transmission.absorption_contributer import (
    AbsenceFromBeam,
    AbsorptionContributer,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.foil_spec import FoilSpec
from dodal.devices.beamlines.i19.transmission.spec_from_config.material_absorption_spectrum_spec import (
    MaterialAbsorptionSpectralConfig,
    MaterialAbsorptionSpectrum,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.system_configuration import (
    SystemConfiguration,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.wheels_spec import (
    WheelsConfig,
    WheelSpec,
)


class MountedFoilAbsorber(AbsorptionContributer):
    def __init__(
        self,
        *,
        system_config: SystemConfiguration,
        wheel_spec: WheelSpec,
        slot_index: int,
    ):

        foil_spec: FoilSpec = wheel_spec.foils[str(slot_index)]
        absorber_material_name: str = foil_spec.absorber.material
        absorption_spec = (
            MaterialAbsorptionSpectralConfig.extract_absorber_material_specifications(
                system_configuration=system_config, material_name=absorber_material_name
            )
        )
        absorption_spectrum: MaterialAbsorptionSpectrum = absorption_spec.as_spectrum()
        flat_geometry = FoilGeometry(
            unit=foil_spec.absorber.thickness.units,
            numerical_value=foil_spec.absorber.thickness.value,
        )
        self.absorber: Final[FixedDepth] = FoilAbsorber(
            spectrum=absorption_spectrum, geometry_model=flat_geometry
        )

    def is_suitable_for_energy(self, *, xray_energy_kev: float) -> bool:
        return self.absorber.is_suitable_for_energy(xray_energy_kev=xray_energy_kev)

    def predict_absorption_at_given_energy(self, *, xray_energy_kev: float) -> float:
        return self.absorber.calculate_absorption_bn(xray_energy_kev=xray_energy_kev)


class ReadableWheelIndexer(Protocol):
    def get_index(self) -> int: ...


class AbsorberWheel:
    def __init__(
        self,
        *,
        index_reader: ReadableWheelIndexer,
        system_config: SystemConfiguration,
        wheel_identifier: str,
    ):
        wheel_spec: WheelSpec = WheelsConfig.extract_wheel_specifications(
            system_configuration=system_config, wheel_identifier=wheel_identifier
        )
        self.id: str = wheel_identifier
        self.index_reader: ReadableWheelIndexer = index_reader
        self.slots: dict[int, AbsorptionContributer] = {
            slot_index: (
                AbsenceFromBeam()
                if slot_index == wheel_spec.out
                else MountedFoilAbsorber(
                    system_config=system_config,
                    wheel_spec=wheel_spec,
                    slot_index=slot_index,
                )
            )
            for slot_index in wheel_spec.all_active_indices
        }

    def predict_absorption_at_given_energy(self, *, xray_energy_kev: float) -> float:
        _present_index = self._read_wheel_motor_present_index()
        return self._predict_absorption(
            xray_energy_kev=xray_energy_kev, index=_present_index
        )

    def residuals_for_all_slots_able_to_contribute(
        self, *, xray_energy_kev: float, demand_bn: float
    ) -> dict[int, float]:
        """Maps filter wheel slot for each motor index against residual demand predicted for use of that slot.

        Arguments:
            demand_bn:  The unfiltered demand budget.
            xray_energy_kev: X-ray photon energy in kiloelectron volts.

        Returns:
            Slot index vs residual demand - after that slot's filter has contributed to meeting the demand.

        Note:
            Slots will be excluded for any of the following reasons:
                - Designated out of bounds,
                - Filter is unsuitable for the requested energy,
            Further slots may be removed at the subsystem level due to limitations there.

        See Also:
            absorption_subsystems.py in this module.
        """
        raw = {
            index: self._predict_residual_demand(
                index=index,
                xray_energy_kev=xray_energy_kev,
                primary_demand_bn=demand_bn,
            )
            for index in self._all_suitable_slots(xray_energy_kev=xray_energy_kev)
        }
        return {i: r for i, r in raw.items() if not r < CANONICAL_NON_ABSORPTION}

    def synthesise_index_change_demand(self, *, index: int) -> dict[str, int]:
        """Builds contribution to future motor demands.

        Arguments:
            index: Identifies filter slot in use of a hypoethical demand.

        Returns: dict suitable for passing on as this wheel's part of a greater AttenuatorMotorPositions instance.

        Note:
            Requests to move motors (motor demands) are the responsibility of the host subsystem,
            which (generally) combines wheel and wedge and knows enough about whether or not to ask.
            This convenience method assembles this wheel's contribution to any potential motor squad demand.
            Change requests trying either to move to a forbidden index, (i.e. not presently in use),
            or the index of the present motor position (i.e. no movement required),
            result in an empty demand dict - as the change request is vetoed.
        """
        _veto_change: bool = (
            index == self._read_wheel_motor_present_index() or index not in self.slots
        )
        return {} if _veto_change else {self.id: index}

    # API methods above

    # Internal methods below

    def _absorber_at_index(self, *, index: int) -> AbsorptionContributer:
        return self.slots[index]

    def _all_suitable_slots(self, *, xray_energy_kev: float) -> list[int]:
        return [
            index
            for index in self.slots
            if self._is_absorber_at_index_available(
                index=index, xray_energy_kev=xray_energy_kev
            )
        ]

    def _is_absorber_at_index_available(
        self, *, index: int, xray_energy_kev: float
    ) -> bool:
        _absorber = self._absorber_at_index(index=index)
        return _absorber.is_suitable_for_energy(xray_energy_kev=xray_energy_kev)

    def _predict_absorption(self, *, xray_energy_kev: float, index: int) -> float:
        """Predicts absorption generally for any given energy and any wheel index.

        Args:
            xray_energy_kev: The x-ray photon energy for the predictive calculation.
            index: selection of specific foil absorber or for the OUT index, an empty slot.

        Returns:
            Absorption prediction in Barnett units.

        Raises:
            ValueError raised if the wheel index is out of bounds (at any energy),
            or if any filter occupying the indicated slot, is unsuitable at the requested energy.
        """
        if index not in self._all_suitable_slots(xray_energy_kev=xray_energy_kev):
            _msg = f"Wheel {self.id} slot {index} is not suitable for use at {xray_energy_kev} keV"
            raise ValueError(_msg)
        _absorber = self._absorber_at_index(index=index)
        return _absorber.predict_absorption_at_given_energy(
            xray_energy_kev=xray_energy_kev
        )

    def _predict_residual_demand(
        self, *, index: int, xray_energy_kev: float, primary_demand_bn: float
    ) -> float:
        _absorber = self._absorber_at_index(index=index)
        return _absorber.predict_residual_demand(
            xray_energy_kev=xray_energy_kev, demand_bn=primary_demand_bn
        )

    def _read_wheel_motor_present_index(self) -> int:
        return self.index_reader.get_index()
