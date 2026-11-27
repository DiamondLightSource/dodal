import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i05_shared.diagnostics import DiagnosticDet
from dodal.devices.current_amplifiers import Femto3xxGainTable


@pytest.fixture
async def mock_diagnostic_det() -> DiagnosticDet:
    async with init_devices(mock=True):
        det = DiagnosticDet("BL05I-EA-DET-01:", name="d3")
    return det


async def test_diagnostic_det_signals_and_naming(mock_diagnostic_det: DiagnosticDet):
    assert mock_diagnostic_det.name == "d3"
    assert mock_diagnostic_det.gain.source == "mock+ca://BL05I-EA-DET-01:GAIN"
    assert mock_diagnostic_det.drain_current.source == "mock+ca://BL05I-EA-DET-01:I"


async def test_diagnostic_det_read_hints(mock_diagnostic_det: DiagnosticDet):
    await assert_reading(
        mock_diagnostic_det,
        {
            "d3-gain": partial_reading(Femto3xxGainTable.SEN_1),
            "d3-drain_current": partial_reading(0.0),
        },
    )
