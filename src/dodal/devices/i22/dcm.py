from typing import Literal

from ophyd_async.core import ConfigSignal, StandardReadable, soft_signal_r_and_setter
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import epics_signal_r


class MonochromatingCrystal(StandardReadable):
    """
    Component of a monochromator, representing a single crystal that can be
    manipulated and introspected.
    """

    def __init__(
        self,
        prefix: str,
        temp_prefix: str = "",
        heater_temp_prefix: str = "",
        usage: Literal["Bragg", "Laue"] | None = None,
        type: str | None = None,
        reflection: tuple[int, int, int] | None = None,
        d_spacing: float | None = None,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            # Positionable Parameters
            self.roll = Motor(prefix + "ROLL")
            self.pitch = Motor(prefix + "PITCH")

            # Temperatures
            self.temp = epics_signal_r(float, temp_prefix)
            self.heater_temp = epics_signal_r(float, heater_temp_prefix)

            # Soft metadata
            # If supplied include crystal details in output of read_configuration
            with self.add_children_as_readables(ConfigSignal):
                if usage is not None:
                    self.crystal_usage, _ = soft_signal_r_and_setter(
                        str, initial_value=usage
                    )
                else:
                    self.crystal_usage = None
                if type is not None:
                    self.crystal_type, _ = soft_signal_r_and_setter(
                        str, initial_value=type
                    )
                else:
                    self.crystal_type = None
                if reflection is not None:
                    self.crystal_reflection, _ = soft_signal_r_and_setter(
                        str, initial_value=reflection
                    )
                else:
                    self.crystal_reflection = None
                if d_spacing is not None:
                    self.crystal_d_spacing, _ = soft_signal_r_and_setter(
                        str, initial_value=d_spacing
                    )
                else:
                    self.crystal_d_spacing = None

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
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            # Positionable Parameters
            self.bragg = Motor(prefix + "BRAGG")
            self.crystal_1 = MonochromatingCrystal(
                prefix + "XSTAL1:",
                temp_prefix=prefix + "PT100-1",
                heater_temp_prefix=prefix + "PT100-2",
            )
            self.crystal_2 = MonochromatingCrystal(
                prefix + "XSTAL2:",
                temp_prefix=prefix + "PT100-4",
                heater_temp_prefix=prefix + "PT100-5",
            )
            self.offset = Motor(prefix + "OFFSET")
            self.perp = Motor(prefix + "PERP")
            self.energy = Motor(prefix + "ENERGY")
            self.wavelength = Motor(prefix + "WAVELENGTH")

            # Assembly Temperatures
            self.backplate_temp = epics_signal_r(float, prefix + "PT100-7")
            self.perp_temp = epics_signal_r(float, prefix + "TC-1")

        super().__init__(name)
