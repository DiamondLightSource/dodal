from unittest.mock import MagicMock, patch

from bluesky.simulators import RunEngineSimulator
from ophyd_async.panda import phase_sorter

from dodal.devices.util.save_panda import _save_panda


def test_save_panda():
    sim_run_engine = RunEngineSimulator()
    panda = MagicMock()
    with (
        patch(
            "dodal.devices.util.save_panda.make_all_devices",
            return_value=({"panda": panda}, {}),
        ) as mock_make_all_devices,
        patch(
            "dodal.devices.util.save_panda.RunEngine",
            return_value=MagicMock(side_effect=sim_run_engine.simulate_plan),
        ),
        patch("dodal.devices.util.save_panda.save_device") as mock_save_device,
    ):
        _save_panda("i03", "panda", "test/file.yml")

        mock_make_all_devices.assert_called_with(
            "dodal.beamlines.i03", include_skipped=False
        )
        mock_save_device.assert_called_with(panda, "test/file.yml", sorter=phase_sorter)
