from os import environ

import pytest

from dodal.devices.smargon import Smargon


@pytest.mark.s03
@pytest.mark.skip(reason="S03 and I03 smargon DISABLED types differ")
async def test_when_smargon_created_against_s03_then_can_connect():
    print(f"EPICS_CA_REPEATER_PORT is {environ['EPICS_CA_REPEATER_PORT']}")
    smargon = Smargon("BL03S-MO-SGON-01:", name="smargon")

    await smargon.connect()
