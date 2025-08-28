# Writing Tests in This Python Project

Testing is essential to maintain the integrity and reliability of the codebase. Follow the guidelines below to write tests for this project effectively.

## Test Organization

- **Unit Tests**: Place unit tests for individual components in the `tests` directory, but take care to mirror the file structure of the `src` folder with the corresponding code files. Use the `test_*.py` naming convention for test files.
- **System Tests**: Tests that interact with DLS infrastructure, network, and filesystem should be placed in the top-level `systems_test` folder. This separation ensures that these tests are easily identifiable and can be run independently from unit tests.

## Writing a test for a device
We aim for high test coverage in dodal with small, modular test functions. To achieve this, we need to test the relevant methods by writing tests for the class/method we are creating or changing, checking for the expected behaviour. We shouldn't need to write tests for parent classes unless we alter their behaviour.

Below, a `StandardReadable` example device is defined which also implements the `Stageable` protocol.

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

In this example, we need to test the `stage`, `unstage`, and `read` methods. The `read` method needs to be tested because we are adding `signal_a` and `signal_b` as readables to the device, so we need to confirm that we get the expected read signals back when this method is called.

We use [pytest](https://docs.pytest.org/en/stable/contents.html) for writing tests in dodal. A core part of this library is the use of fixtures. A fixture is a function decorated with `@pytest.fixture` that provides setup/teardown or reusable test data for your tests. It is defined once and can be reused across multiple tests. Fixtures are mainly used to define devices and then inject them into each test.

To help set up a device, they are created with the `init_devices(mock=True)` function from `ophyd_async.core`, which automatically initialises the device in mock mode. The `RunEngine` is present when creating a device to ensure there is an event loop available when connecting signals. The `RunEngine` fixture itself is defined in `dodal/tests/conftest.py`, which is a special file recognised by `pytest`. It defines fixtures that are automatically available to any test in the same directory (and its subdirectories) without needing to import them. This is useful for defining common setup code once without duplicating it across test files.

In order for `pytest` to detect something as a test, a function should begin with `test_*`. The test function should be self-descriptive about what it is testing, and it is acceptable (even encouraged) to have longer names for test functions for clarity.

```Python
import asyncio
from unittest.mock import ANY

import pytest
from bluesky import RunEngine
from bluesky import plan_stubs as bps
from ophyd_async.core import OnOff, init_devices
from ophyd_async.testing import assert_reading, get_mock_put, partial_reading
from dodal.device.my_device import  MyDevice


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

For testing the read output of a device, there are some handy functions defined in `ophyd-async` to aid with this. `assert_reading` allows us to compare the readings generated from a `Readable` device to the expected results. `partial_reading` wraps the value given in a mapping like `{"value": ANY}`, so we are actually checking that the reading matches the expected structure.

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

Once we have written the tests, we need to check that they pass and how much coverage there is. `pytest` should automatically detect your tests and display one of the following icons within the VSCode IDE:
- Grey circle (not run yet)
- Green circle with a tick (test passed)
- Red circle with a cross (test failed)

You can also check code coverage by right-clicking on the test icon and selecting `Run with coverage`. This will re-run the test and highlight line numbers in your file:
- Green = covered by tests
- Red = not covered (and ideally should be tested)

To view all tests inside dodal, use the `Test Explorer` panel (flask icon) in VSCode. It displays all of your tests in a hierarchy, which you can run individually or in groups. It also shows the pass/fail icons mentioned above. Clicking on an item will run all tests beneath it in the hierarchy.

You can also run all tests in the command line via the command:
`tox -e tests`

This will also display each Python module’s percentage of code coverage achieved.

If you find that your tests are being skipped or not recognised by `pytest`, check for any syntax errors as this will block the tests being found. You can also check to see if there is an error output at the very bottom of the `Test Explorer` panel. This is usually caused by invalid syntax in your test file, or by circular dependencies in the code you are testing.
