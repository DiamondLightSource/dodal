from .specs import SpecsDetector
from .util import to_binding_energy, to_kinetic_energy
from .vgscienta import VGScientaDetector

TElectronAnalyserDetectorImpl = VGScientaDetector | SpecsDetector

__all__ = ["to_binding_energy", "to_kinetic_energy", "TElectronAnalyserDetectorImpl"]
