from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_rw
from ophyd_async.epics.motor import Motor


class CcmcPositions(StrictEnum):
    OUT = "Out of Beam"
    XTAL_2000 = "Xtal_2000"
    XTAL_2250 = "Xtal_2250"
    XTAL_2500 = "Xtal_2500"


class Ccmc(StandardReadable):
    """
    Device to move the channel cut monochromator (ccmc). CCMC has three
    choices of crystal (Xtal for short). Setting energy is by means of a
    multi-positioner. The positions are named after the nominal energies of the
    crystals. Select one of the crystals from the list. This causes the Y motor
    to move that crystal into the beam and other motors have to align the angles
    correctly.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.x = Motor(prefix + "X")
        self.y = Motor(prefix + "Y")
        self.z = Motor(prefix + "Z")

        # ToDo this is piezo motor, so need to have correct class as PVs are different
        self.y_rotation = epics_signal_rw(
            float,
            read_pv=prefix + "ROTY:POS:RD",
            write_pv=prefix + "ROTY:MOV:WR",
        )

        self.pos_select = epics_signal_rw(CcmcPositions, prefix + "CRYSTAL:MP:SELECT")

        super().__init__(name)
