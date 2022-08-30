from ophyd import Component, Device, FormattedComponent

from dodal.devices.fast_grid_scan import FastGridScan
from dodal.devices.motors import I03Smargon
from dodal.devices.slit_gaps import SlitGaps
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.undulator import Undulator
from dodal.devices.zebra import Zebra


class FGSComposite(Device):
    """A device consisting of all the Devices required for a fast gridscan."""

    fast_grid_scan = Component(FastGridScan, "-MO-SGON-01:FGS:")

    zebra = Component(Zebra, "-EA-ZEBRA-01:")

    undulator = FormattedComponent(Undulator, "{insertion_prefix}-MO-SERVC-01:")

    synchrotron = FormattedComponent(Synchrotron)
    slit_gaps = Component(SlitGaps, "-AL-SLITS-04:")

    sample_motors: I03Smargon = Component(I03Smargon, "-MO-SGON-01:")

    def __init__(self, insertion_prefix: str, *args, **kwargs):
        self.insertion_prefix = insertion_prefix
        super().__init__(*args, **kwargs)
