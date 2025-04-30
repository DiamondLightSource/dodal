import asyncio
import functools
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from ophyd import Device
from ophyd.device import Device as OphydV1Device
from ophyd.sim import FakeEpicsSignal
from ophyd_async.core import Device as OphydV2Device
from ophyd_async.core import StandardReadable

from dodal.common.beamlines import beamline_utils
from dodal.devices.eiger import EigerDetector
from dodal.devices.focusing_mirror import FocusingMirror
from dodal.devices.motors import XYZPositioner
from dodal.devices.smargon import Smargon
from dodal.log import LOGGER
from dodal.utils import DeviceInitializationController


@pytest.fixture(autouse=True)
def flush_event_loop_on_finish(event_loop):
    # wait for the test function to complete
    yield None

    if pending_tasks := asyncio.all_tasks(event_loop):
        LOGGER.warning(f"Waiting for pending tasks to complete {pending_tasks}")
        event_loop.run_until_complete(asyncio.gather(*pending_tasks))


def test_instantiate_function_makes_supplied_device():
    device_types = [XYZPositioner, Smargon]
    for device in device_types:
        dev = beamline_utils.device_instantiation(
            device, device.__name__, "", False, True, None
        )
        assert isinstance(dev, device)


def test_instantiating_different_device_with_same_name():
    dev1 = beamline_utils.device_instantiation(  # noqa
        XYZPositioner, "device", "", False, True, None
    )
    with pytest.raises(TypeError):
        dev2 = beamline_utils.device_instantiation(
            Smargon, "device", "", False, True, None
        )
    beamline_utils.clear_device("device")
    dev2 = beamline_utils.device_instantiation(  # noqa
        Smargon, "device", "", False, True, None
    )
    assert dev1.name == dev2.name
    assert type(dev1) is not type(dev2)
    assert dev1 not in beamline_utils.ACTIVE_DEVICES.values()
    assert dev2 in beamline_utils.ACTIVE_DEVICES.values()


def test_instantiate_v1_function_fake_makes_fake():
    eiger: EigerDetector = beamline_utils.device_instantiation(
        EigerDetector, "eiger", "", True, True, None
    )
    assert isinstance(eiger, Device)
    assert isinstance(eiger.stale_params, FakeEpicsSignal)


def test_instantiate_v2_function_fake_makes_fake(RE):
    fake_smargon: Smargon = beamline_utils.device_instantiation(
        Smargon, "smargon", "", True, True, None
    )
    assert isinstance(fake_smargon, StandardReadable)
    assert fake_smargon.omega.user_setpoint.source.startswith("mock+ca")


@pytest.mark.parametrize(
    "kwargs,expected_timeout", [({}, 5.0), ({"timeout": 15.0}, 15.0)]
)
def test_wait_for_v1_device_connection_passes_through_timeout(kwargs, expected_timeout):
    device = OphydV1Device(name="")
    device.wait_for_connection = MagicMock()

    beamline_utils.wait_for_connection(device, **kwargs)

    device.wait_for_connection.assert_called_once_with(timeout=expected_timeout)


@pytest.mark.parametrize(
    "kwargs,expected_timeout", [({}, 5.0), ({"timeout": 15.0}, 15.0)]
)
@patch(
    "dodal.common.beamlines.beamline_utils.v2_device_wait_for_connection",
    new=AsyncMock(),
)
def test_wait_for_v2_device_connection_passes_through_timeout(
    kwargs, expected_timeout, RE
):
    device = OphydV2Device()
    device.connect = MagicMock()

    beamline_utils.wait_for_connection(device, **kwargs)

    device.connect.assert_called_once_with(
        mock=ANY,
        timeout=expected_timeout,
    )


def dummy_mirror() -> FocusingMirror:
    mirror = MagicMock(spec=FocusingMirror)
    connect = AsyncMock()
    mirror.connect = connect

    def set_name(name: str):
        mirror.name = name  # type: ignore

    mirror.set_name.side_effect = set_name
    mirror.set_name("")
    return mirror


@beamline_utils.device_factory(mock=True)
def dummy_mirror_as_device_factory() -> FocusingMirror:
    return dummy_mirror()


@beamline_utils.device_factory(mock=True)
@functools.lru_cache
def cached_dummy_mirror_as_device_factory() -> FocusingMirror:
    return dummy_mirror()


def test_device_controller_name_propagated():
    mirror = dummy_mirror_as_device_factory(name="foo")
    assert mirror.name == "foo"


def test_device_controller_connection_is_lazy():
    mirror = dummy_mirror_as_device_factory(name="foo")
    assert mirror.connect.call_count == 0  # type: ignore


def test_device_controller_eager_connect(RE):
    mirror = dummy_mirror_as_device_factory(connect_immediately=True)
    assert mirror.connect.call_count == 1  # type: ignore


@pytest.mark.parametrize(
    "factory",
    [
        dummy_mirror_as_device_factory,
        # The second test case confirms that if, for some reason, we use a device
        # factory decorated with @lru_cache, dodal is not affected and will still cache
        # the same device instance internally. We actually also use lru_cache
        # internally so this test case is just a sanity check to prove it is
        # idempotent.
        cached_dummy_mirror_as_device_factory,
    ],
)
def test_device_cached(factory: DeviceInitializationController):
    mirror_1 = factory()
    mirror_2 = factory()
    assert mirror_1 is mirror_2


def test_device_cache_can_be_cleared():
    mirror_1 = dummy_mirror_as_device_factory()
    dummy_mirror_as_device_factory.cache_clear()

    mirror_2 = dummy_mirror_as_device_factory()
    assert mirror_1 is not mirror_2


def test_skip(RE):
    skip = True

    def _skip() -> bool:
        return skip

    controller = beamline_utils.device_factory(skip=_skip)(dummy_mirror)

    assert isinstance(controller, DeviceInitializationController)
    assert controller.skip

    skip = False
    assert not controller.skip
