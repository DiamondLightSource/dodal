from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_r


class ReadOnlyEnergyAndAttenuator(StandardReadable):
    """A read-only device to get collection metadata, in use for jungfrau."""

    def __init__(self, prefix: str, name: str = "") -> None:
        # NOTE prefix in this case should only be the beamline prefix
        self.transmission = epics_signal_r(float, f"{prefix}-OP-ATTN-01:MATCH")
        self.wavelength = epics_signal_r(float, f"{prefix}-MO-DCM-01:LAMBDA")
        self.energy = epics_signal_r(float, "-MO-DCM-01:ENERGY.RBV")
        self.intensity = epics_signal_r(float, "-EA-XBPM-01:SumAll:MeanValue_RBV")
        self.flux_xbpm2 = epics_signal_r(float, "-EA-FLUX-01:XBPM-02")
        self.flux_xbpm3 = epics_signal_r(float, "-EA-FLUX-01:XBPM-03")
        self.shutter = epics_signal_r(str, "-PS-SHTR-01:CON")
        self.slow_shutter = epics_signal_r(str, "-EA-SHTR-02:M32")
        self.detector_distance = epics_signal_r(float, "-EA-DET-01:Z.RBV")
        super().__init__(name)
