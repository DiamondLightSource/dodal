from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class StripeChoice(StrictEnum):
    EH1_RH = "EH1-Rh"
    EH1_SI = "EH1-Si"
    EH1_PT = "EH1-Pt"
    EH2_RH = "EH2-Rh"
    EH2_SI = "EH2-Si"
    EH2_PT = "EH2-Pt"


class MirrorStripes(StandardReadable):
    """A simple device that can move the mirror stripes and set the voltages on I19."""

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            # Setting this will trigger the motors move and the voltages change
            self.stripe_choice = epics_signal_rw(StripeChoice, f"{prefix}stripeChoice")
            self.is_busy = epics_signal_r(int, f"{prefix}stripeChange:BUSY")
            self.error_code = epics_signal_r(
                int, f"{prefix}stripeVoltageChange:reportErrors.VALB"
            )
            self.error_message = epics_signal_r(
                str, f"{prefix}stripeVoltageChange:reportErrors.VALA"
            )
        super().__init__(name=name)
