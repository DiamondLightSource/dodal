from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    StrictEnum,
    derived_signal_r,
)
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.motors import XYZStage


class ChannelCutMonochromatorPositions(StrictEnum):
    OUT = "Out of Beam"
    XTAL_2000 = "Xtal_2000"
    XTAL_2250 = "Xtal_2250"
    XTAL_2500 = "Xtal_2500"


ccmc_lower_limit = 1500.0
ccmc_upper_limit = 3000.0
error_message = "Can not get energy value in eV from ccmc position: "


class ChannelCutMonochromator(
    StandardReadable, Movable[ChannelCutMonochromatorPositions]
):
    """
    Device to move the channel cut monochromator (ccmc). CCMC has three
    choices of crystal (Xtal for short). Setting energy is by means of a
    multi-positioner. The positions are named after the nominal energies of the
    crystals. To change energy select one of the crystals from the list.
    This causes the Y motor to move that crystal into the beam and other
    motors have to align the angles correctly.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
    ) -> None:
        """
        Parameters
        ----------
        prefix:
            Beamline specific part of the PV
        name:
            Name of the device
        """
        with self.add_children_as_readables():
            # crystal motors
            self._xyz = XYZStage(prefix)
            # piezo motor in epics
            self._y_rotation = epics_signal_rw(
                float,
                read_pv=prefix + "ROTY:POS:RD",
                write_pv=prefix + "ROTY:MOV:WR",
            )
            # Must be a CHILD as read() must return this signal
            self.crystal = epics_signal_rw(
                ChannelCutMonochromatorPositions, prefix + "CRYSTAL:MP:SELECT"
            )

        # energy derived signal as property
        self.energy_in_ev = derived_signal_r(
            self._convert_pos_to_ev, pos_signal=self.crystal
        )
        super().__init__(name=name)

    def _convert_pos_to_ev(self, pos_signal: ChannelCutMonochromatorPositions) -> float:
        if pos_signal != ChannelCutMonochromatorPositions.OUT:
            energy = float(str(pos_signal.value).split("Xtal_")[1])
            if ccmc_lower_limit < energy < ccmc_upper_limit:
                return energy
        raise ValueError(error_message)

    @AsyncStatus.wrap
    async def set(self, value: ChannelCutMonochromatorPositions) -> None:
        await self.crystal.set(value, wait=True)
