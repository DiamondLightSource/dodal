from ophyd_async.core import StandardReadable, StrictEnum, derived_signal_r
from ophyd_async.epics.core import epics_signal_rw


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
            self.beam_size_x = derived_signal_r(
                self._get_beam_size_x, horizontal=self.horizontal, derived_units="um"
            )
            self.beam_size_y = derived_signal_r(
                self._get_beam_size_y, vertical=self.vertical, derived_units="um"
            )

        super().__init__(name)

    def _get_beam_size_x(self, horizontal: HFocusMode) -> int:
        beam_x = BEAM_SIZES[horizontal.removeprefix("HMFM")][0]
        return beam_x

    def _get_beam_size_y(self, vertical: VFocusMode) -> int:
        beam_y = BEAM_SIZES[vertical.removeprefix("VMFM")][1]
        return beam_y
