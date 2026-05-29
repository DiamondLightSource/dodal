from enum import StrEnum

from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class StripeChoice(StrictEnum):
    EH1_RH = "EH1-Rh"
    EH1_SI = "EH1-Si"
    EH1_PT = "EH1-Pt"
    EH2_RH = "EH2-Rh"
    EH2_SI = "EH2-Si"
    EH2_PT = "EH2-Pt"


class Stripe(StrEnum):
    RH = "Rh"
    SI = "Si"
    PT = "Pt"


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

    # This will need some mapping
    def select_stripe_based_on_energy(self, energy_in_kev: float) -> Stripe:
        # Pt: 20-30 KeV
        # Rh: 10-20 KeV
        # Si: 5-10 KeV
        if 5 <= energy_in_kev < 10:
            return Stripe.SI
        elif 10 <= energy_in_kev < 20:
            return Stripe.RH
        elif 20 <= energy_in_kev < 30:
            return Stripe.PT
        else:
            raise ValueError("Energy request out of bounds")
        # TBC - needs improvement
