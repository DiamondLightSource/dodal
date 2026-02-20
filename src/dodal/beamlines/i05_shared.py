from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i05_shared import (
    APPLE_KNOT_EXCLUSION_ZONES,
    Grating,
    M3MJ6Mirror,
    energy_to_gap_converter,
    energy_to_phase_converter,
)
from dodal.devices.common_mirror import XYZPiezoSwitchingMirror
from dodal.devices.insertion_device import (
    Apple2,
    UndulatorGap,
    UndulatorLockedPhaseAxes,
)
from dodal.devices.insertion_device.apple_knot_controller import (
    AppleKnotController,
    AppleKnotPathFinder,
)
from dodal.devices.insertion_device.energy import BeamEnergy, InsertionDeviceEnergy
from dodal.devices.insertion_device.polarisation import InsertionDevicePolarisation
from dodal.devices.motors import XYZPitchYawRollStage
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.devices.synchrotron import Synchrotron
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i05-shared")
PREFIX = BeamlinePrefix("i05-shared", "I")

devices = DeviceManager()


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices.factory()
def pgm() -> PlaneGratingMonochromator:
    return PlaneGratingMonochromator(
        prefix=f"{PREFIX.beamline_prefix}-OP-PGM-01:",
        grating=Grating,
    )


@devices.factory()
def id_gap() -> UndulatorGap:
    return UndulatorGap(prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:")


@devices.factory()
def id_phase() -> UndulatorLockedPhaseAxes:
    return UndulatorLockedPhaseAxes(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        top_outer="PL",
        btm_inner="PU",
    )


@devices.factory()
def id(
    id_gap: UndulatorGap,
    id_phase: UndulatorLockedPhaseAxes,
) -> Apple2[UndulatorLockedPhaseAxes]:
    """i05 insertion device."""
    return Apple2[UndulatorLockedPhaseAxes](id_gap=id_gap, id_phase=id_phase)


@devices.factory()
def m1_collimating_mirror() -> XYZPitchYawRollStage:
    return XYZPitchYawRollStage(prefix=f"{PREFIX.beamline_prefix}-OP-COL-01:")


# will connect after https://jira.diamond.ac.uk/browse/I05-731
@devices.factory(skip=True)
def m3mj6_switching_mirror() -> XYZPiezoSwitchingMirror:
    return XYZPiezoSwitchingMirror(
        prefix=f"{PREFIX.beamline_prefix}-OP-SWTCH-01:",
        mirrors=M3MJ6Mirror,
    )


@devices.factory()
def id_controller(
    id: Apple2[UndulatorLockedPhaseAxes],
) -> AppleKnotController[UndulatorLockedPhaseAxes]:
    return AppleKnotController[UndulatorLockedPhaseAxes](
        apple=id,
        gap_energy_motor_converter=energy_to_gap_converter,
        phase_energy_motor_converter=energy_to_phase_converter,
        path_finder=AppleKnotPathFinder(APPLE_KNOT_EXCLUSION_ZONES),
    )


@devices.factory()
def id_energy(
    id_controller: AppleKnotController[UndulatorLockedPhaseAxes],
) -> InsertionDeviceEnergy:
    return InsertionDeviceEnergy(id_controller=id_controller)


@devices.factory()
def id_polarisation(
    id_controller: AppleKnotController[UndulatorLockedPhaseAxes],
) -> InsertionDevicePolarisation:
    return InsertionDevicePolarisation(id_controller=id_controller)


@devices.factory()
def energy(
    id_energy: InsertionDeviceEnergy, pgm: PlaneGratingMonochromator
) -> BeamEnergy:
    return BeamEnergy(id_energy=id_energy, mono=pgm.energy)
