from ophyd_async.core import (
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    derived_signal_r,
)
from ophyd_async.epics.core import epics_signal_rw


class CCMCPositions(StrictEnum):
    OUT = "Out of Beam"
    XTAL_2000 = "Xtal_2000"
    XTAL_2250 = "Xtal_2250"
    XTAL_2500 = "Xtal_2500"


class CCMC(StandardReadable):
    """
    Device to move the channel cut monochromator (ccmc). CCMC has three
    choices of crystal (Xtal for short). Setting energy is by means of a
    multi-positioner. The positions are named after the nominal energies of the
    crystals. Select one of the crystals from the list. This causes the Y motor
    to move that crystal into the beam and other motors have to align the angles
    correctly.
    """

    def __init__(
        self,
        prefix: str,
        positions: type[StrictEnum],
        name: str = "",
    ) -> None:
        """
        Parameters
        ----------
        prefix:
            Beamline specific part of the PV
        positions:
            The Enum for the positions names.
        name:
            Name of the device
        """
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            # normal motors in epics
            self.x = epics_signal_rw(float, prefix + "X")
            self.y = epics_signal_rw(float, prefix + "Y")
            self.z = epics_signal_rw(float, prefix + "Z")
            # piezo motor in epics
            self.y_rotation = epics_signal_rw(
                float,
                read_pv=prefix + "ROTY:POS:RD",
                write_pv=prefix + "ROTY:MOV:WR",
            )

        with self.add_children_as_readables():
            # Must be a CHILD as read() must return this signal
            self.pos_select = epics_signal_rw(positions, prefix + "CRYSTAL:MP:SELECT")
            self.energy_in_ev = derived_signal_r(
                self._convert_pos_to_eV, pos_signal=self.pos_select
            )

        super().__init__(name)

    def _convert_pos_to_eV(self, pos_signal: CCMCPositions) -> float:
        if pos_signal != CCMCPositions.OUT:
            return float(str(pos_signal.value).split("Xtal_")[1])
        return 0.0
