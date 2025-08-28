# Writing Tests in This Python Project

Testing is essential to maintain the integrity and reliability of the codebase. Follow the guidelines below to write tests for this project effectively.

## Test Organization

- **Unit Tests**: Place unit tests for individual components in the `tests` directory, but take care to mirror the file structure of the `src` folder with the corresponding code files. Use the `test_*.py` naming convention for test files.
- **System Tests**: Tests that interact with DLS infrastructure, network, and filesystem should be placed in the top-level `systems_test` folder. This separation ensures that these tests are easily identifiable and can be run independently from unit tests.

## Writing a test for a device
We aim for high test coverage in dodal with small modular test functions. To achieve this, we need test the relevant methods by writing tests for the class/method were creating/changing for the expected behaviour. We shouldn't need to right tests for parent classes unless we alter the behaviour. Below a StandardReadable example device is defined which also implements the Stageable protocal.  

```Python
from bluesky import RunEngine
from bluesky.protocols import Stageable
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
            self.signal_b = epics_signal_rw(OnOff, prefix + "B")

        super().__init__(name)

    @AsyncStatus.wrap
    async def stage(self):
        """
        Setup device by moving signal_a to ON.
        """
        await asyncio.gather(super().stage(), self.signal_b.set(OnOff.ON))

    @AsyncStatus.wrap
    async def unstage(self):
        """
        Once device is finished, set signal_b back to OFF.
        """
        await asyncio.gather(super().stage(), self.signal_b.set(OnOff.OFF))
```

In this example, we need to test the `stage`, `unstage`, and `read` methods. The `read` method needs to be tested as were adding `signal_a` and `signal_b` as readables to the device, so we need to test we get the expected read signals back when this method is called.

We use pytest [pytest](https://docs.pytest.org/en/stable/contents.html) for writing tests in dodal. A core part of this librabry is the use of fixtures. A fixture is a function you decorate with `@pytest.fixture` that provides setup/teardown or reusable test data for your tests. It is defined onced and can be reused across multiple tests. They are mainly used to define devices 
and then inject them into each test. To help setup a device, they are created with the `init_devices(mock=True)` funtion from `ophyd_async.core` which auto initalises the device in mock mode. The `RunEngine` is present when creating a device to ensure there is an event loop present when connecting siganls. The `RunEngine` `pytest.fixture` is defined in `dodal/conftest.py` which is a special file tha is recognised by `pytest`. It defines fixtures that are automatically available to any test in the same directory (and its subdirectories) without needing to import them. It is useful for defining common setup code without having to import it in each test file.


```Python
import asyncio
from unittest.mock import ANY

import pytest
from bluesky import RunEngine
from bluesky import plan_stubs as bps
from ophyd_async.core import OnOff, init_devices
from ophyd_async.testing import assert_reading, get_mock_put, partial_reading


# RunEngine is needed to make sure there is an event loop when creating device.
@pytest.fixture
async def sim_my_device(RE: RunEngine) -> MyDevice:
    async with init_devices(mock=True):
        sim_my_device = MyDevice("TEST:")
    return sim_my_device


def test_my_device_stage(sim_my_device: MyDevice, RE: RunEngine) -> None:
    RE(bps.stage(sim_my_device, wait=True), wait=True)
    get_mock_put(sim_my_device.signal_b).assert_called_once_with(OnOff.ON, wait=True)


def test_my_device_unstage(sim_my_device: MyDevice, RE: RunEngine) -> None:
    RE(bps.unstage(sim_my_device, wait=True), wait=True)
    get_mock_put(sim_my_device.signal_b).assert_called_once_with(OnOff.OFF, wait=True)


async def test_my_device_read(sim_my_device: MyDevice, RE: RunEngine) -> None:
    prefix = sim_my_device.name
    await assert_reading(
        sim_my_device,
        {
            f"{prefix}-signal_a": partial_reading(ANY),
            f"{prefix}-signal_b": partial_reading(ANY),
        },
    )

```
In order for pytest to detect something is a test, a function should begin with `test_*`. The test function should be self descriptive on exactly what it is testing, and it is more acceptable to have longer function names for test functions for this purpose.

For testing the read output of the device, there are some handy testing functions defined in ophyd-async to aid with this. `assert_reading` allows us to compare the readings generated from a `Readable` device is as we expect. `partial_reading` wraps the value given in a value mapping `{"value": ANY}` so we're actually checking the reading matches the following:

```Python
    prefix = sim_my_device.name
    await assert_reading(
        sim_my_device,
        {
            f"{prefix}-signal_a" : {"value": ANY},
            f"{prefix}-signal_b" : {"value": ANY},
        }
    )
```

Now we have written the tests, we need to check they pass and how much coverage there is. `pytest` should automatically detect your test are valid tests and display a grey circle (hasn't been tested yet), green circle with tick (test has passed) or a red circle with a cross (test failed) icon next to your tests. You can also check to see the code coverage by right clicking this icon and selecting "Run with coverage". This will re-run the test and also highlight the line numbers of your class with green and red. Green means it is covered by tests, read means it is not covered (and ideally should be added).

To view all tests inside of dodal, you can use the `Test Explorer` panel (picture of a flask). It displays all of your tests as a hierarchy which you can run independently to other tests. It will dispaly the icons mentioned above with each test and clicking on one will run all tests underneath the object in the hierarchy. You can also run all tests via the command `tox -e tests`. This will also display each python module percetnage of code coverage achieved.

If you are finding that your tests are being skipped and not recognised by pytest, then check to see if there is any error output at the very bottom of the `Test Explorer` panel. This is usually caused by invalid syntax in your test or the code you are testing has circular dependencies. 
