from os import fspath
from pathlib import Path

MOCK_DAQ_CONFIG_PATH = fspath(Path(__file__).parent)

__all__ = ["MOCK_DAQ_CONFIG_PATH"]
