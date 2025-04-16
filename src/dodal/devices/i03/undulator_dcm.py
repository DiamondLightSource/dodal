import asyncio

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, Reference, StandardReadable

from dodal.common.beamlines.beamline_parameters import get_beamline_parameters
from dodal.devices.i03.dcm import DCM
from dodal.devices.undulator import Undulator
from dodal.log import LOGGER

ENERGY_TIMEOUT_S: float = 30.0


class UndulatorDCM(StandardReadable, Movable[float]):
    """
    Composite device to handle changing beamline energies, wraps the Undulator and the
    DCM. The DCM has a motor which controls the beam energy, when it moves, the
    Undulator gap may also have to change to enable emission at the new energy.
    The relationship between the two motor motor positions is provided via a lookup
    table.

    Calling unulator_dcm.set(energy) will move the DCM motor, perform a table lookup
    and move the Undulator gap motor if needed. So the set method can be thought of as
    a comprehensive way to set beam energy.

    This class will be removed in the future. Use the separate Undulator and DCM devices
    instead. See https://github.com/DiamondLightSource/dodal/issues/1092
    """

    def __init__(
        self,
        undulator: Undulator,
        dcm: DCM,
        daq_configuration_path: str,
        prefix: str = "",
        name: str = "",
    ):
        self.undulator_ref = Reference(undulator)
        self.dcm_ref = Reference(dcm)

        # These attributes are just used by hyperion for lookup purposes
        self.pitch_energy_table_path = (
            daq_configuration_path + "/lookup/BeamLineEnergy_DCM_Pitch_converter.txt"
        )
        self.roll_energy_table_path = (
            daq_configuration_path + "/lookup/BeamLineEnergy_DCM_Roll_converter.txt"
        )
        # I03 configures the DCM Perp as a side effect of applying this fixed value to the DCM Offset after an energy change
        # Nb this parameter is misleadingly named to confuse you
        self.dcm_fixed_offset_mm = get_beamline_parameters(
            daq_configuration_path + "/domain/beamlineParameters"
        )["DCM_Perp_Offset_FIXED"]

        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        await self.undulator_ref().raise_if_not_enabled()
        await asyncio.gather(
            self.dcm_ref().energy_in_kev.set(value, timeout=ENERGY_TIMEOUT_S),
            self.undulator_ref().set(value),
        )
        # DCM Perp pitch
        LOGGER.info(f"Adjusting DCM offset to {self.dcm_fixed_offset_mm} mm")
        await self.dcm_ref().offset_in_mm.set(self.dcm_fixed_offset_mm)
