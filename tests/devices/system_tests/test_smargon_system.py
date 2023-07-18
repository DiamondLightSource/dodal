import pytest

from dodal.devices.smargon import Smargon


@pytest.mark.s03
def test_when_smargon_created_against_s03_then_can_connect():
    smargon = Smargon("BL03S-MO-SGON-01:", name="smargon")

    smargon.wait_for_connection()
