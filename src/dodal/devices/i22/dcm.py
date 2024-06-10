from dataclasses import dataclass
from typing import Literal

from ophyd_async.core import ConfigSignal, StandardReadable, soft_signal_r_and_setter
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import epics_signal_r


@dataclass(frozen=True, unsafe_hash=True)
class CrystalMetadata:
    """
    Metadata used in the NeXus format,
    see https://manual.nexusformat.org/classes/base_classes/NXcrystal.html
    """

    usage: Literal["Bragg", "Laue"] | None = None
    type: str | None = None
    reflection: tuple[int, int, int] | None = None
    d_spacing: float | None = None


class DoubleCrystalMonochromator(StandardReadable):
    """
    A double crystal monochromator (DCM), used to select the energy of the beam.

    perp describes the gap between the 2 DCM crystals which has to change as you alter
    the angle to select the requested energy.

    offset ensures that the beam exits the DCM at the same point, regardless of energy.
    """

    def __init__(
        self,
        motion_prefix: str,
        temperature_prefix: str,
        crystal_1_metadata: CrystalMetadata | None = None,
        crystal_2_metadata: CrystalMetadata | None = None,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            # Positionable Parameters
            self.bragg = Motor(motion_prefix + "BRAGG")
            self.offset = Motor(motion_prefix + "OFFSET")
            self.perp = Motor(motion_prefix + "PERP")
            self.energy = Motor(motion_prefix + "ENERGY")
            self.crystal_1_roll = Motor(motion_prefix + "XTAL1:ROLL")
            self.crystal_2_roll = Motor(motion_prefix + "XTAL2:ROLL")
            self.crystal_2_pitch = Motor(motion_prefix + "XTAL2:PITCH")

            # Temperatures
            self.backplate_temp = epics_signal_r(float, temperature_prefix + "PT100-7")
            self.perp_temp = epics_signal_r(float, temperature_prefix + "TC-1")
            self.crystal_1_temp = epics_signal_r(float, temperature_prefix + "PT100-1")
            self.crystal_1_heater_temp = epics_signal_r(
                float, temperature_prefix + "PT100-2"
            )
            self.crystal_2_temp = epics_signal_r(float, temperature_prefix + "PT100-4")
            self.crystal_2_heater_temp = epics_signal_r(
                float, temperature_prefix + "PT100-5"
            )

        # Soft metadata
        # If supplied include crystal details in output of read_configuration
        crystal_1_metadata = crystal_1_metadata or CrystalMetadata()
        crystal_2_metadata = crystal_2_metadata or CrystalMetadata()
        with self.add_children_as_readables(ConfigSignal):
            if crystal_1_metadata.usage is not None:
                self.crystal_1_usage, _ = soft_signal_r_and_setter(
                    str, initial_value=crystal_1_metadata.usage
                )
            else:
                self.crystal_1_usage = None
            if crystal_1_metadata.type is not None:
                self.crystal_1_type, _ = soft_signal_r_and_setter(
                    str, initial_value=crystal_1_metadata.type
                )
            else:
                self.crystal_1_type = None
            if crystal_1_metadata.reflection is not None:
                self.crystal_1_reflection, _ = soft_signal_r_and_setter(
                    str, initial_value=crystal_1_metadata.reflection
                )
            else:
                self.crystal_1_reflection = None
            if crystal_1_metadata.d_spacing is not None:
                self.crystal_1_d_spacing, _ = soft_signal_r_and_setter(
                    str, initial_value=crystal_1_metadata.d_spacing
                )
            else:
                self.crystal_1_d_spacing = None
            if crystal_2_metadata.usage is not None:
                self.crystal_2_usage, _ = soft_signal_r_and_setter(
                    str, initial_value=crystal_2_metadata.usage
                )
            else:
                self.crystal_2_usage = None
            if crystal_2_metadata.type is not None:
                self.crystal_2_type, _ = soft_signal_r_and_setter(
                    str, initial_value=crystal_2_metadata.type
                )
            else:
                self.crystal_2_type = None
            if crystal_2_metadata.reflection is not None:
                self.crystal_2_reflection, _ = soft_signal_r_and_setter(
                    str, initial_value=crystal_2_metadata.reflection
                )
            else:
                self.crystal_2_reflection = None
            if crystal_2_metadata.d_spacing is not None:
                self.crystal_2_d_spacing, _ = soft_signal_r_and_setter(
                    str, initial_value=crystal_2_metadata.d_spacing
                )
            else:
                self.crystal_2_d_spacing = None

        super().__init__(name)
