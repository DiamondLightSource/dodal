import pytest

from dodal.devices.beamlines import b07, b07_shared, i09
from dodal.devices.electron_analyser.base import GenericElectronAnalyserDetector
from dodal.devices.electron_analyser.specs import SpecsDetector
from dodal.devices.electron_analyser.vgscienta import VGScientaDetector


@pytest.fixture(params=["ew4000", "b07b_specs150"])
def sim_detector(
    request: pytest.FixtureRequest,
    ew4000: VGScientaDetector[i09.LensMode, i09.PsuMode, i09.PassEnergy],
    b07b_specs150: SpecsDetector[b07.LensMode, b07_shared.PsuMode],
) -> GenericElectronAnalyserDetector:
    detectors = [ew4000, b07b_specs150]
    for detector in detectors:
        if detector.name == request.param:
            return detector

    raise ValueError(f"Detector with name '{request.param}' not found")
