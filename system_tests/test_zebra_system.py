import pytest

from dodal.devices.zebra import ArmDemand, Zebra


@pytest.fixture()
async def zebra():
    zebra = Zebra(name="zebra", prefix="BL03S-EA-ZEBRA-01:")
    yield zebra
    await zebra.pc.arm.set(ArmDemand.DISARM)


@pytest.mark.s03
async def test_arm(zebra: Zebra):
    arming_status = zebra.pc.arm.set(ArmDemand.ARM)
    assert not zebra.pc.is_armed()
    await arming_status
    assert zebra.pc.is_armed()
    zebra.pc.arm.set(ArmDemand.DISARM)


@pytest.mark.s03
async def test_disarm(zebra: Zebra):
    await zebra.pc.arm.set(ArmDemand.ARM)
    assert zebra.pc.is_armed()
    await zebra.pc.arm.set(ArmDemand.DISARM)
    assert not zebra.pc.is_armed()
