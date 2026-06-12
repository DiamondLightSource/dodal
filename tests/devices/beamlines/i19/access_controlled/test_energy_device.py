import json
from unittest.mock import AsyncMock, patch

import pytest
from ophyd_async.core import SignalR, init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i19.access_controlled.blueapi_device import (
    HEADERS,
    HutchState,
)
from dodal.devices.beamlines.i19.access_controlled.energy_device import (
    AccessControlledEnergyComposite,
    OutOfRangeEnergyRequestError,
)
from dodal.devices.beamlines.i19.mirror_stripes import StripeChoice


@pytest.fixture
def eh1_energy_device() -> AccessControlledEnergyComposite:
    with init_devices(mock=True):
        device = AccessControlledEnergyComposite(
            "", HutchState.EH1, "cm12345-1", "mock_eh1_energy"
        )
    device.url = "http://test.url"
    set_mock_value(device.energy_in_kev, 17.9973)
    set_mock_value(device.wavelength_in_a, 0.6889)
    return device


@pytest.fixture
def eh2_energy_device() -> AccessControlledEnergyComposite:
    with init_devices(mock=True):
        device = AccessControlledEnergyComposite(
            "", HutchState.EH2, "cm12345-1", "mock_eh1_energy"
        )
    device.url = "http://test.url"
    set_mock_value(device.energy_in_kev, 17.9973)
    set_mock_value(device.wavelength_in_a, 0.6889)
    return device


@pytest.mark.parametrize("hutch_name", [HutchState.EH1, HutchState.EH2])
def test_device_created_without_errors(hutch_name: HutchState):
    test_device = AccessControlledEnergyComposite(
        "", hutch_name, "cm12345-1", "fake-device"
    )
    assert isinstance(test_device, AccessControlledEnergyComposite)
    assert isinstance(test_device.energy_in_kev, SignalR)
    assert isinstance(test_device.wavelength_in_a, SignalR)


async def test_energy_and_wavelength_can_be_read_from_device(
    eh1_energy_device: AccessControlledEnergyComposite,
):
    await assert_reading(
        eh1_energy_device,
        {
            "mock_eh1_energy-energy_in_kev": partial_reading(17.9973),
            "mock_eh1_energy-wavelength_in_a": partial_reading(0.6889),
        },
    )


def test_get_stripe_choice_errors_if_energy_out_of_bounds(
    eh2_energy_device: AccessControlledEnergyComposite,
):
    with pytest.raises(OutOfRangeEnergyRequestError):
        eh2_energy_device._get_stripe_choice_from_energy_request(2.0)


@pytest.mark.parametrize(
    "energy_request, expected_stripe",
    [
        (8.4, StripeChoice.EH1_SI),
        (17.9, StripeChoice.EH1_RH),
        (25.3, StripeChoice.EH1_PT),
    ],
)
def test_correct_stripe_selected_for_eh1(
    energy_request: float,
    expected_stripe: StripeChoice,
    eh1_energy_device: AccessControlledEnergyComposite,
):
    stripe = eh1_energy_device._get_stripe_choice_from_energy_request(energy_request)
    assert stripe == expected_stripe


@pytest.mark.parametrize(
    "energy_request, expected_stripe",
    [
        (6.2, StripeChoice.EH2_SI),
        (14.86, StripeChoice.EH2_RH),
        (28.7, StripeChoice.EH2_PT),
    ],
)
def test_correct_stripe_returned_for_eh2(
    energy_request: float,
    expected_stripe: StripeChoice,
    eh2_energy_device: AccessControlledEnergyComposite,
):
    stripe = eh2_energy_device._get_stripe_choice_from_energy_request(energy_request)
    assert stripe == expected_stripe


@pytest.mark.parametrize(
    "energy_request, expected_stripe",
    [
        (8.4, StripeChoice.EH1_SI),
        (17.9, StripeChoice.EH1_RH),
        (25.3, StripeChoice.EH1_PT),
    ],
)
async def test_device_makes_correct_rest_call_for_eh1(
    energy_request: float,
    expected_stripe: StripeChoice,
    eh1_energy_device: AccessControlledEnergyComposite,
):
    expected_params = {
        "name": "change_energy_plan",
        "params": {
            "experiment_hutch": "EH1",
            "access_device": "access_control",
            "energy_in_kev": energy_request,
            "stripe_choice": expected_stripe.value,
        },
        "instrument_session": "cm12345-1",
    }
    expected_params_json = json.dumps(expected_params)
    with (
        patch(
            "dodal.devices.beamlines.i19.access_controlled.blueapi_device.ClientSession.post"
        ) as mock_post,
        patch(
            "dodal.devices.beamlines.i19.access_controlled.blueapi_device.ClientSession.put"
        ) as mock_put,
        patch(
            "dodal.devices.beamlines.i19.access_controlled.blueapi_device.ClientSession.get"
        ) as mock_get,
    ):
        mock_post.return_value.__aenter__.return_value = (mock_response := AsyncMock())
        mock_response.ok = True
        mock_response.json.return_value = {"task_id": "abc0-3fg8"}
        mock_put.return_value.__aenter__.return_value = (
            mock_put_response := AsyncMock()
        )
        mock_put_response.ok = True
        mock_get.return_value.__aenter__.return_value = (
            mock_get_response := AsyncMock()
        )
        mock_get_response.json.return_value = {"is_complete": True, "errors": []}

        await eh1_energy_device.set(energy_request)

        mock_post.assert_called_with(
            "/tasks", data=expected_params_json, headers=HEADERS
        )
        mock_put.assert_called_with(
            "/worker/task", data='{"task_id": "abc0-3fg8"}', headers=HEADERS
        )


@pytest.mark.parametrize(
    "energy_request, expected_stripe",
    [
        (6.2, StripeChoice.EH2_SI),
        (14.86, StripeChoice.EH2_RH),
        (28.7, StripeChoice.EH2_PT),
    ],
)
async def test_device_makes_correct_rest_call_for_eh2(
    energy_request: float,
    expected_stripe: StripeChoice,
    eh2_energy_device: AccessControlledEnergyComposite,
):
    expected_params = {
        "name": "change_energy_plan",
        "params": {
            "experiment_hutch": "EH2",
            "access_device": "access_control",
            "energy_in_kev": energy_request,
            "stripe_choice": expected_stripe.value,
        },
        "instrument_session": "cm12345-1",
    }
    expected_params_json = json.dumps(expected_params)
    with (
        patch(
            "dodal.devices.beamlines.i19.access_controlled.blueapi_device.ClientSession.post"
        ) as mock_post,
        patch(
            "dodal.devices.beamlines.i19.access_controlled.blueapi_device.ClientSession.put"
        ) as mock_put,
        patch(
            "dodal.devices.beamlines.i19.access_controlled.blueapi_device.ClientSession.get"
        ) as mock_get,
    ):
        mock_post.return_value.__aenter__.return_value = (mock_response := AsyncMock())
        mock_response.ok = True
        mock_response.json.return_value = {"task_id": "abc0-3fg8"}
        mock_put.return_value.__aenter__.return_value = (
            mock_put_response := AsyncMock()
        )
        mock_put_response.ok = True
        mock_get.return_value.__aenter__.return_value = (
            mock_get_response := AsyncMock()
        )
        mock_get_response.json.return_value = {"is_complete": True, "errors": []}

        await eh2_energy_device.set(energy_request)

        mock_post.assert_called_with(
            "/tasks", data=expected_params_json, headers=HEADERS
        )
        mock_put.assert_called_with(
            "/worker/task", data='{"task_id": "abc0-3fg8"}', headers=HEADERS
        )
