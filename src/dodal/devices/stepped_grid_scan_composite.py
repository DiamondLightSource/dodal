from ophyd import Component, FormattedComponent

from dodal.devices.aperturescatterguard import AperturePositions, ApertureScatterguard
from dodal.devices.logging_ophyd_device import InfoLoggingDevice
from dodal.devices.s4_slit_gaps import S4SlitGaps
from dodal.devices.smargon import Smargon
from dodal.devices.stepped_grid_scan import SteppedGridScan
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.undulator import Undulator
from dodal.devices.zebra import Zebra


class SteppedGridScanComposite(InfoLoggingDevice):
    """A device consisting of all the Devices required for a stepped grid scan."""

    stepped_grid_scan = Component(SteppedGridScan, "-MO-SGON-01:FGS:")

    zebra = Component(Zebra, "-EA-ZEBRA-01:")

    undulator = FormattedComponent(Undulator, "{insertion_prefix}-MO-SERVC-01:")

    synchrotron = FormattedComponent(Synchrotron)
    s4_slit_gaps = Component(S4SlitGaps, "-AL-SLITS-04:")

    sample_motors: Smargon = Component(Smargon, "")

    aperture_scatterguard: ApertureScatterguard = Component(ApertureScatterguard, "")

    def __init__(
        self,
        insertion_prefix: str,
        aperture_positions: AperturePositions = None,
        *args,
        **kwargs,
    ):
        self.insertion_prefix = insertion_prefix
        super().__init__(*args, **kwargs)
        if aperture_positions is not None:
            self.aperture_scatterguard.load_aperture_positions(aperture_positions)
