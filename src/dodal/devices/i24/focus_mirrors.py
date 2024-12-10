from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_rw

from dodal.common.signal_utils import create_hardware_backed_soft_signal


class HFocusMode(StrictEnum):
    FOCUS_10 = "HMFMfocus10"
    FOCUS_20D = "HMFMfocus20d"
    FOCUS_30D = "HMFMfocus30d"
    FOCUS_50D = "HMFMfocus50d"
    FOCUS_1050D = "HMFMfocus1030d"
    FOCUS_3010D = "HMFMfocus3010d"


class VFocusMode(StrictEnum):
    FOCUS_10 = "VMFMfocus10"
    FOCUS_20D = "VMFMfocus20d"
    FOCUS_30D = "VMFMfocus30d"
    FOCUS_50D = "VMFMfocus50d"
    FOCUS_1030D = "VMFMfocus1030d"
    FOCUS_3010D = "VMFMfocus3010d"


BEAM_SIZES = {
    "focus10": [7, 7],
    "focus20d": [20, 20],
    "focus30d": [30, 30],
    "focus50d": [50, 50],
    "focus1030d": [10, 30],
    "focus3010d": [30, 10],
}


class FocusMirrorsMode(StandardReadable):
    """A small device to read the focus mode and work out the beam size."""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.horizontal = epics_signal_rw(HFocusMode, prefix + "G1:TARGETAPPLY")
        self.vertical = epics_signal_rw(VFocusMode, prefix + "G0:TARGETAPPLY")

        with self.add_children_as_readables():
            self.beam_size_x = create_hardware_backed_soft_signal(
                int, self._get_beam_size_x, units="um"
            )
            self.beam_size_y = create_hardware_backed_soft_signal(
                int, self._get_beam_size_y, units="um"
            )

        super().__init__(name)

    async def _get_beam_size_x(self) -> int:
        h_mode = await self.horizontal.get_value()
        beam_x = BEAM_SIZES[h_mode.removeprefix("HMFM")][0]
        return beam_x

    async def _get_beam_size_y(self) -> int:
        v_mode = await self.vertical.get_value()
        beam_y = BEAM_SIZES[v_mode.removeprefix("VMFM")][1]
        return beam_y
