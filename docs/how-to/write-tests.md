# Writing Tests in This Python Project

Testing is essential to maintain the integrity and reliability of the codebase. Follow the guidelines below to write tests for this project effectively.

## Test Organization

- **Unit Tests**: Place unit tests for individual components in the `tests` directory, but take care to mirror the file structure of the `src` folder with the corresponding code files. Use the `test_*.py` naming convention for test files.
- **System Tests**: Tests that interact with DLS infrastructure, network, and filesystem should be placed in the top-level `systems_test` folder. This separation ensures that these tests are easily identifiable and can be run independently from unit tests.

## Writing a test for a device
Below a StandardReadable example device is defined which also implements the Stageable protocal.  

```Python
import asyncio
from bluesky.protocals import Stageable
from ophyd_async.core import AsyncStatus, OnOff, StandardReadable
from ophyd_async.epics.core import epics_signal_rw

class MyDevice(StandardReadable, Stageable):
    """
    Example device demostrating how to test stage, unstage and read methods.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        """
        Constructor for setting up instance of device.

        Parameters:
            prefix: Base PV used for connecting signals.
            name: Name of the device.
        """
        with self.add_children_as_readables():
            self.signal_a = epics_signal_rw(float, prefix + "A")
            self.siganl_b = epics_signal_rw(OnOff, prefix + "B")

        super().__init__(name)

    @AsyncStatus.wrap
    async def stage(self):
        """
        Setup device by moving signal_a to ON.
        """
        await asyncio.gather(super().stage(), self.siganl_b.set(OnOff.ON))

    @AsyncStatus.wrap
    async def unstage(self):
        """
        Once device is finished, set signal_b back to OFF.
        """
        await asyncio.gather(super().stage(), self.siganl_b.set(OnOff.OFF))
```

We aim for high test coverage in dodal with small modular test functions. To achieve this, we need test the relevant methods by writing tests for the class/method were creating/changing for the expected behaviour and not unnecessary any parent classes. In this example, we need to test the `stage`, `unstage`, and `read` methods. The `read` method needs to be tested as were adding `signal_a` and `signal_b` as readables to the device, so we need to test we get the expected read signals back.

We use pytest [pytest](https://docs.pytest.org/en/stable/contents.html) for writing unit tests in dodal. A core part of this librabry is the use of fixtures. A `pytest.fixture` is a function you decorate with `@pytest.fixture` that provides setup/teardown or reusable test data for your tests. It is defined onced and can be reused across multiple tests. They are mainly used to define devices 
and then inject them into each test. To help setup a device, they are created with the `init_devices(mock=True)` funtion from `ophyd_async.core` which auto initalises the device in mock mode. The `RunEngine` is present when creating a device to ensure there is an event loop present when connecting siganls. The `RunEngine` `pytest.fixture` is defined in `dodal/conftest.py` which is a special file tha is recognised by `pytest`. It defines fixtures that are automatically available to any test in the same directory (and its subdirectories) without needing to import them. It is useful for defining common setup code without having to import it in each test file.


```Python
from unittest.mock import ANY
import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading
from dodal.devices.my_device import MyDevice
from bluesky import plan_stubs as bps


#RunEngine is needed to make sure there is an event loop when creating device.
@pytest.fixture
async def sim_my_device(RE: RunEngine) -> MyDevice:
    async with init_devices(mock=True):
        sim_my_device = MyDevice("TEST:")
    return sim_my_device


def test_my_device_stage(sim_my_device: MyDevice, RE: RunEngine) -> None:
    sim_detector.signal_b = AsyncMock()
    RE(bps.stage(sim_detector, wait=True), wait=True)
    sim_detector.siganl_b.assert_awaited_once_with(OnOff.On)


def test_my_device_unstage(sim_my_device: MyDevice, RE: RunEngine) -> None:
    sim_detector.signal_b = AsyncMock()
    RE(bps.unstage(sim_detector, wait=True), wait=True)
    sim_detector.siganl_b.assert_awaited_once_with(OnOff.OFF)


async def test_my_device_read(sim_my_device: MyDevice, RE: RunEngine) -> None:
    prefix = sim_my_device.name
    await assert_reading(
        sim_my_device,
        {
            f"{prefix}-signal_a" : partial_reading(ANY),
            f"{prefix}-signal_b" : partial_reading(ANY),
        }
    )
```


- callback on mock puts
