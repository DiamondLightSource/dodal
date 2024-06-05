from dataclasses import dataclass
from typing import Literal

from ophyd_async.core import ConfigSignal, StandardReadable, soft_signal_r_and_setter
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import epics_signal_r


@dataclass
class CrystalMetadata:
    """
    Metadata used in the NeXus format,
    see https://manual.nexusformat.org/classes/base_classes/NXcrystal.html
    """

    usage: Literal["Bragg", "Laue"] | None = None
    type: str | None = None
    reflection: tuple[int, int, int] | None = None
    d_spacing: float | None = None


class MonochromatingCrystal(StandardReadable):
    """
    Component of a monochromator, representing a single crystal that can be
    manipulated and introspected.
    """

    def __init__(
        self,
        prefix: str,
        metadata: CrystalMetadata,
        temp_prefix: str = "",
        heater_temp_prefix: str = "",
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            # Positionable Parameters
            self.roll = Motor(prefix + "ROLL")
            self.pitch = Motor(prefix + "PITCH")

            # # Temperatures
            self.temp = epics_signal_r(float, temp_prefix)
            self.heater_temp = epics_signal_r(float, heater_temp_prefix)

        # Soft metadata
        # If supplied include crystal details in output of read_configuration
        with self.add_children_as_readables(ConfigSignal):
            if metadata.usage is not None:
                self.usage, _ = soft_signal_r_and_setter(
                    str, initial_value=metadata.usage
                )
            else:
                self.usage = None
            if metadata.type is not None:
                self.type, _ = soft_signal_r_and_setter(
                    str, initial_value=metadata.type
                )
            else:
                self.type = None
            if metadata.reflection is not None:
                self.reflection, _ = soft_signal_r_and_setter(
                    str, initial_value=metadata.reflection
                )
            else:
                self.reflection = None
            if metadata.d_spacing is not None:
                self.d_spacing, _ = soft_signal_r_and_setter(
                    str, initial_value=metadata.d_spacing
                )
            else:
                self.d_spacing = None

        super().__init__(name)


class DoubleCrystalMonochromator(StandardReadable):
    """
    A double crystal monochromator (DCM), used to select the energy of the beam.

    perp describes the gap between the 2 DCM crystals which has to change as you alter
    the angle to select the requested energy.

    offset ensures that the beam exits the DCM at the same point, regardless of energy.
    """

    def __init__(
        self,
        prefix: str,
        crystal_1_metadata: CrystalMetadata | None = None,
        crystal_2_metadata: CrystalMetadata | None = None,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            # Positionable Parameters
            self.crystal_1 = MonochromatingCrystal(
                prefix + "XSTAL1:",
                metadata=crystal_1_metadata or CrystalMetadata(),
                temp_prefix=prefix + "PT100-1",
                heater_temp_prefix=prefix + "PT100-2",
            )
            self.crystal_2 = MonochromatingCrystal(
                prefix + "XSTAL2:",
                metadata=crystal_2_metadata or CrystalMetadata(),
                temp_prefix=prefix + "PT100-4",
                heater_temp_prefix=prefix + "PT100-5",
            )

            self.bragg = Motor(prefix + "BRAGG")
            self.offset = Motor(prefix + "OFFSET")
            self.perp = Motor(prefix + "PERP")
            self.energy = Motor(prefix + "ENERGY")

            # Assembly Temperatures
            self.backplate_temp = epics_signal_r(float, prefix + "PT100-7")
            self.perp_temp = epics_signal_r(float, prefix + "TC-1")

        super().__init__(name)
