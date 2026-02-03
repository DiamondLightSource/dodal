import json
from unittest.mock import AsyncMock, patch

import pytest
from ophyd_async.core import SignalR, init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.i19.access_controlled.blueapi_device import HEADERS, HutchState
from dodal.devices.i19.access_controlled.piezo_control import (
    AccessControlledPiezoActuator,
    FocusingMirrorName,
)


@pytest.fixture
def eh1_vfm_piezo() -> AccessControlledPiezoActuator:
    with init_devices(mock=True):
        v_piezo = AccessControlledPiezoActuator(
            "",
            FocusingMirrorName.VFM,
            HutchState.EH1,
            "cm12345-1",
            name="mock_vfm_piezo",
        )
    v_piezo.url = "http://test.url"
    set_mock_value(v_piezo.readback, 1.0)
    return v_piezo


@pytest.fixture
def eh2_hfm_piezo() -> AccessControlledPiezoActuator:
    with init_devices(mock=True):
        h_piezo = AccessControlledPiezoActuator(
            "",
            FocusingMirrorName.HFM,
            HutchState.EH2,
            "cm12345-1",
            name="mock_hfm_piezo",
        )
    h_piezo.url = "http://test.url"
    set_mock_value(h_piezo.readback, 1.0)
    return h_piezo


@pytest.mark.parametrize(
    "hutch_name, mirror_type",
    [
        (HutchState.EH1, FocusingMirrorName.HFM),
        (HutchState.EH2, FocusingMirrorName.VFM),
    ],
)
def test_device_created_without_errors(
    hutch_name: HutchState, mirror_type: FocusingMirrorName
):
    test_device = AccessControlledPiezoActuator(
        "", mirror_type, hutch_name, "cm12345-1", "fake_piezo"
    )
    assert isinstance(test_device, AccessControlledPiezoActuator)
    assert isinstance(test_device.readback, SignalR)


async def test_vfm_piezo_rbv_value_can_be_read(
    eh1_vfm_piezo: AccessControlledPiezoActuator,
):
    await assert_reading(
        eh1_vfm_piezo, {"mock_vfm_piezo-readback": partial_reading(1.0)}
    )


async def test_hfm_piezo_rbv_value_can_be_read(
    eh2_hfm_piezo: AccessControlledPiezoActuator,
):
    await assert_reading(
        eh2_hfm_piezo, {"mock_hfm_piezo-readback": partial_reading(1.0)}
    )


async def test_vfm_piezo_makes_the_correct_rest_call(
    eh1_vfm_piezo: AccessControlledPiezoActuator,
):
    voltage_demand = 3.2
    expected_params = {
        "name": "apply_voltage_to_piezo",
        "params": {
            "experiment_hutch": "EH1",
            "access_device": "access_control",
            "voltage_demand": voltage_demand,
            "focus_mirror": "vfm",
        },
        "instrument_session": "cm12345-1",
    }
    expected_params_json = json.dumps(expected_params)
    with (
        patch(
            "dodal.devices.i19.access_controlled.blueapi_device.ClientSession.post"
        ) as mock_post,
        patch(
            "dodal.devices.i19.access_controlled.blueapi_device.ClientSession.put"
        ) as mock_put,
        patch(
            "dodal.devices.i19.access_controlled.blueapi_device.ClientSession.get"
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

        await eh1_vfm_piezo.set(voltage_demand)

        mock_post.assert_called_with(
            "/tasks", data=expected_params_json, headers=HEADERS
        )
        mock_put.assert_called_with(
            "/worker/task", data='{"task_id": "abc0-3fg8"}', headers=HEADERS
        )


async def test_hfm_piezo_makes_the_correct_rest_call(
    eh2_hfm_piezo: AccessControlledPiezoActuator,
):
    voltage_demand = 1.5
    expected_params = {
        "name": "apply_voltage_to_piezo",
        "params": {
            "experiment_hutch": "EH2",
            "access_device": "access_control",
            "voltage_demand": voltage_demand,
            "focus_mirror": "hfm",
        },
        "instrument_session": "cm12345-1",
    }
    expected_params_json = json.dumps(expected_params)
    with (
        patch(
            "dodal.devices.i19.access_controlled.blueapi_device.ClientSession.post"
        ) as mock_post,
        patch(
            "dodal.devices.i19.access_controlled.blueapi_device.ClientSession.put"
        ) as mock_put,
        patch(
            "dodal.devices.i19.access_controlled.blueapi_device.ClientSession.get"
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

        await eh2_hfm_piezo.set(voltage_demand)

        mock_post.assert_called_with(
            "/tasks", data=expected_params_json, headers=HEADERS
        )
        mock_put.assert_called_with(
            "/worker/task", data='{"task_id": "abc0-3fg8"}', headers=HEADERS
        )
