from enum import StrEnum

from ophyd_async.core import AsyncStatus, StandardReadableFormat
from ophyd_async.epics.core import epics_signal_r

from dodal.devices.beamlines.i19.access_controlled.blueapi_device import (
    HutchState,
    OpticsBlueAPIDevice,
)
from dodal.devices.beamlines.i19.access_controlled.hutch_access import (
    ACCESS_DEVICE_NAME,
)
from dodal.devices.beamlines.i19.mirror_stripes import StripeChoice


class OutOfRangeEnergyRequestError(ValueError):
    pass


class Stripes(StrEnum):
    RH = "Rh"
    SI = "Si"
    PT = "Pt"


CHANGE_ENERGY_PLAN_NAME = "change_energy_plan"


class AccessControlledEnergyComposite(OpticsBlueAPIDevice):
    """I19-specific device to change the beamline energy.

    This device will send a REST call to the blueapi instance controlling the optics
    hutch running on the I19 cluster, which will evaluate the current hutch in use vs
    the hutch sending the request and decide if the plan will be run or not.
    As the two hutches are located in series, checking the hutch in use is necessary to
    avoid accidentally operating the common optics devices (dcm, undulator, focusing
    mirrors and stripes) from one hutch while the other has beamtime.

    The name of the hutch that wants to change the energy, as well as a commissioning
    directory to act as a placeholder for the instrument_session, should be passed to the
    device upon instantiation.

    The plan to change the energy also involves moving the mirror stripes and the stripe
    selection is hutch-dependent, so the choice of stripe needs to be done internally to
    this device and passed to the plan.

    For details see the architecture described in
    https://diamondlightsource.github.io/i19-bluesky/main/explanations/decisions/0004-optics-blueapi-architecture.html
    """

    def __init__(
        self,
        dcm_prefix: str,
        hutch: HutchState,
        instrument_session: str = "",
        name: str = "",
    ) -> None:
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.energy_in_kev = epics_signal_r(float, f"{dcm_prefix}ENERGY")
            self.wavelength_in_a = epics_signal_r(float, f"{dcm_prefix}WAVELENGTH")
        super().__init__(hutch, instrument_session, name)

    def _get_stripe_choice_from_energy_request(
        self, energy_in_kev: float
    ) -> StripeChoice:
        """Returns the correct value to set to the mirror stripes, considering the
        energy request and the invoking hutch.

        Energy ranges:
            SI: [5KeV, 10KeV)
            RH: [10KeV, 20KeV)
            PT: [20KeV, 30KeV)
        """
        if 5 <= energy_in_kev < 10:
            stripe = Stripes.SI
        elif 10 <= energy_in_kev < 20:
            stripe = Stripes.RH
        elif 20 <= energy_in_kev < 30:
            stripe = Stripes.PT
        else:
            raise OutOfRangeEnergyRequestError(
                f"The requested energy at {energy_in_kev} KeV is out of range"
            )
        _choice = f"{self._invoking_hutch}-{stripe}"
        return StripeChoice(_choice)

    @AsyncStatus.wrap
    async def set(self, value: float):
        # Given value, get stripe type from energy range and get correct enum
        selected_stripe = self._get_stripe_choice_from_energy_request(value)
        request_params = {
            "name": CHANGE_ENERGY_PLAN_NAME,
            "params": {
                "experiment_hutch": self._invoking_hutch,
                "access_device": ACCESS_DEVICE_NAME,
                "energy_in_kev": value,
                "stripe_choice": selected_stripe.value,
            },
            "instrument_session": self.instrument_session,
        }
        await super().set(request_params)
