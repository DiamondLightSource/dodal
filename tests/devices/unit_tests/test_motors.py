from unittest.mock import ANY, MagicMock, call, patch

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading

from dodal.devices.motors import MotorGroup, SixAxisGonio, safe_identifier


@pytest.fixture
def six_axis_gonio(RE: RunEngine):
    with init_devices(mock=True):
        gonio = SixAxisGonio("")

    return gonio


async def test_reading_six_axis_gonio(six_axis_gonio: SixAxisGonio):
    await assert_reading(
        six_axis_gonio,
        {
            "gonio-omega": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "gonio-kappa": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "gonio-phi": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "gonio-z": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "gonio-y": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "gonio-x": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
        },
    )


def test_motor_group_creates_correct_motor_children():
    group_name = "mygroup"
    m1_name = "motor_one"
    m1_pv = "PV1"
    m2_name = "motor_two"
    m2_pv = "PV2"

    with patch("dodal.devices.motors.Motor") as MockMotor:
        mock_m1 = MagicMock()
        mock_m2 = MagicMock()
        MockMotor.side_effect = [mock_m1, mock_m2]

        group = MotorGroup({m1_name: m1_pv, m2_name: m2_pv}, name=group_name)
        # is the group name set correctly?
        assert group.name == group_name

        # fields with expected names?
        assert hasattr(group, m1_name)
        assert hasattr(group, m2_name)

        # are children motors?
        assert getattr(group, m1_name) is mock_m1
        assert getattr(group, m2_name) is mock_m2

        # have motors been instantiated with expected PVs and names?
        MockMotor.assert_has_calls([call(m1_pv, m1_name), call(m2_pv, m2_name)])


def test_safe_identifier():
    """the function MotorGroup uses to produce safely named attributes"""
    raw_to_safe = {
        "motor a": "motor_a",
        "2nd-motor": "_2nd_motor",
        "**motor": "_motor",
        "@@@another@one": "_another_one",
        "&%self&%": "_self_",
    }

    safe_ids = [safe_identifier(raw) for raw in raw_to_safe.keys()]
    assert safe_ids == list(raw_to_safe.values())


def test_motor_group_sanitises_names():
    group = MotorGroup({"motor a": ""})
    assert hasattr(group, "motor_a")
