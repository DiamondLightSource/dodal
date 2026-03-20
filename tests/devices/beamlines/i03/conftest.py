import pytest


@pytest.fixture(autouse=True)
def use_beamline_i03(monkeypatch):
    monkeypatch.setenv("BEAMLINE", "i03")
