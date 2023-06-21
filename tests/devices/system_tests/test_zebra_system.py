import pytest

from dodal.devices.zebra import ArmDemand, Zebra


@pytest.fixture()
def zebra():
    zebra = Zebra(name="zebra", prefix="BL03S-EA-ZEBRA-01:")
    yield zebra
    zebra.pc.disarm().wait(10.0)


@pytest.mark.s03
def test_arm(zebra: Zebra):
    arming_status = zebra.pc.arm.set(ArmDemand.ARM)
    assert not zebra.pc.is_armed()
    arming_status.wait(10.0)
    assert zebra.pc.is_armed()
    zebra.pc.arm.set(ArmDemand.DISARM).wait(10.0)


@pytest.mark.s03
def test_disarm(zebra: Zebra):
    zebra.pc.arm.set(ArmDemand.ARM).wait(10.0)
    assert zebra.pc.is_armed()
    zebra.pc.arm.set(ArmDemand.DISARM).wait(10.0)
    assert not zebra.pc.is_armed()
