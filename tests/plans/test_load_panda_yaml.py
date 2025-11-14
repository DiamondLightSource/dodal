from unittest.mock import MagicMock, patch

import pytest
from bluesky.plan_stubs import null
from bluesky.run_engine import RunEngine
from ophyd_async.fastcs.panda import HDFPanda

from dodal.plans.load_panda_yaml import load_panda_from_yaml


@pytest.fixture
def panda():
    return HDFPanda


def get_test_plan(*args):
    yield from null()
    return "retrieved_settings"


@patch("dodal.plans.load_panda_yaml.YamlSettingsProvider")
@patch("dodal.plans.load_panda_yaml.retrieve_settings")
@patch("dodal.plans.load_panda_yaml.apply_panda_settings")
def test_load_panda_from_yaml(
    mock_apply_panda_settings: MagicMock,
    mock_retrieve_settings: MagicMock,
    mock_settings_provider: MagicMock,
    panda: HDFPanda,
    tmpdir,
    run_engine: RunEngine,
):
    test_file = "test"
    mock_settings_provider.return_value = (mock_settings_return := MagicMock())
    mock_retrieve_settings.side_effect = get_test_plan

    run_engine(
        load_panda_from_yaml(
            tmpdir,
            test_file,
            panda,
        )
    )

    mock_settings_provider.assert_called_once_with(tmpdir)
    mock_retrieve_settings.assert_called_once_with(
        mock_settings_return, test_file, panda
    )
    mock_apply_panda_settings.assert_called_once_with("retrieved_settings")
