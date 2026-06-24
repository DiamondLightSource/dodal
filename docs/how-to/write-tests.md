# Writing Tests in This Python Project

Testing is essential to maintain the integrity and reliability of the codebase. Follow the guidelines below to write tests for this project effectively.

## Test Organization

- **Unit Tests**: Place unit tests for individual components in the `tests` directory, but take care to mirror the file structure of the `src` folder with the corresponding code files. Use the `test_*.py` naming convention for test files.
- **System Tests**: Tests that interact with DLS infrastructure, network, and filesystem should be placed in the top-level `systems_test` folder. This separation ensures that these tests are easily identifiable and can be run independently from unit tests.

Useful functions for testing that can be reused across multiple tests for common devices and for external plan repositories belong in the `dodal/testing` directory.


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

        Args:
            prefix (str): Base PV used for connecting signals.
            name (str): Name of the device.
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

In this example, we need to test the `stage` and `unstage` methods. For more complex devices, it is also a good idea to test the `read` method to confirm that we get the expected read signals back when this method is called.

We use [pytest](https://docs.pytest.org/en/stable/contents.html) for writing tests in dodal. A core part of this library is the use of fixtures. A fixture is a function decorated with `@pytest.fixture` that provides setup/teardown or reusable test data for your tests. It is defined once and can be reused across multiple tests. Fixtures are mainly used to define devices and then inject them into each test. 

Common fixtures, such as the `run_engine` used in the below tests, can also be defined in `dodal/tests/conftest.py`, which is a special file recognised by `pytest`. These fixtures are automatically available to any test in the same directory (and its subdirectories) without needing to import them. This is useful for defining common setup code once without duplicating it across test files.

Devices are set up in the fixture using the `init_devices(mock=True)` function from `ophyd_async.core`, which automatically initialises the device in mock mode. 

In order for `pytest` to detect something as a test, a function should begin with `test_*`. The test function should be self-descriptive about what it is testing, and it is acceptable (even encouraged) to have longer names for test functions for clarity.

```Python
import asyncio

import pytest
from bluesky import RunEngine
from bluesky import plan_stubs as bps
from ophyd_async.core import OnOff, init_devices
from ophyd_async.testing import assert_reading, get_mock_put, partial_reading
from dodal.device.my_device import  MyDevice


@pytest.fixture
async def sim_my_device() -> MyDevice:
    async with init_devices(mock=True):
        sim_my_device = MyDevice("TEST:")
    return sim_my_device


def test_my_device_stage(sim_my_device: MyDevice, run_engine: RunEngine) -> None:
    run_engine(bps.stage(sim_my_device, wait=True), wait=True)
    get_mock_put(sim_my_device.signal_b).assert_called_once_with(OnOff.ON, wait=True)


def test_my_device_unstage(sim_my_device: MyDevice, run_engine: RunEngine) -> None:
    run_engine(bps.unstage(sim_my_device, wait=True), wait=True)
    get_mock_put(sim_my_device.signal_b).assert_called_once_with(OnOff.OFF, wait=True)
```

You should test the output of a device when the device has many signals read and you want to ensure the correct ones are read at the correct times, or when the `read` method of it or one of its signals (e.g. a DerivedSignal) requires testing. Functions are defined in `ophyd-async` to aid with this. `assert_reading` allows us to compare the readings generated from a `Readable` device to the expected results.

```Python
async def test_my_device_read(sim_my_device: MyDevice, run_engine: RunEngine) -> None:
    prefix = sim_my_device.name
    await assert_reading(
        sim_my_device,
        {
            f"{prefix}-signal_a": partial_reading(OnOff.ON),
            f"{prefix}-signal_b": partial_reading(0),
        },
    )
```

`partial_reading` wraps the value given in a mapping like `{"value": ANY}`, so we are actually checking that the reading matches the expected structure.

```Python
    prefix = sim_my_device.name
    await assert_reading(
        sim_my_device,
        {
            f"{prefix}-signal_a" : {"value": OnOff.ON},
            f"{prefix}-signal_b" : {"value": 0},
        }
    )
```

## Mocking `ConfigClient`

Beamlines and devices may depend on the daq-config-server `ConfigClient` to retrieve configuration files. These files are often stored on the DLS filesystem and contain configuration data that determines device behaviour.

For example, an insertion device may use a calibration file containing polynomial coefficients that convert photon energy into insertion device gap for different polarisation modes. A device may retrieve this information using a `ConfigClient`:

```python
from pathlib import Path

from daq_config_server import ConfigClient

from dodal.device_manager import DeviceManager
from dodal.devices.my_device import MyDevice

LOOKUPTABLE_DIR = (
    "/dls_sw/iXX/software/gda/workspace_git/"
    "gda-diamond.git/configurations/iXX/lookupTables"
)
LOOKUP_FILE_NAME = "JIDEnergy2GapCalibrations.csv"

devices = DeviceManager()


@devices.fixture
def config_client() -> ConfigClient:
    return ConfigClient()


@devices.factory()
def my_device(config_client: ConfigClient) -> MyDevice:
    return MyDevice(
        config_client=config_client,
        path=Path(LOOKUPTABLE_DIR, LOOKUP_FILE_NAME),
    )
```

### Directly mocking return values

If a test does not need to exercise file parsing logic, it is often simpler to mock the ConfigClient response directly rather than creating a test file and configuring a parser.

```python
from unittest.mock import MagicMock

from daq_config_server.models.lookup_tables.insertion_device import (
    UndulatorEnergyGapLookupTable,
)

@pytest.fixture
def mock_config_client():
    mock_config_client = MagicMock()
    mock_config_client.get_file_contents = MagicMock(
        return_value=UndulatorEnergyGapLookupTable(
            rows=[
                [5700, 5.4606],
                [7000, 6.045],
                [9700, 6.404],
            ],
        )
    )
    return mock_config_client
```
This approach is appropriate when:

* The test only cares about the behaviour of the device or component consuming the configuration data.
* The contents of the configuration file are not relevant to the test.
* The parsing logic is tested elsewhere.

In these cases, mocking the return value directly avoids unnecessary coupling to file formats or test data files.

Use the below method if you need the data to come from a file for a unit test.

### Using the mock_config_client fixture to read files
Unit tests should not communicate with the real daq-config-server or read files from the DLS filesystem.

Dodal provides a `mock_config_client` fixture in `dodal.testing.fixtures.config_client`. This fixture replaces the real service with a lightweight implementation that reads test files directly from the local filesystem.

Most tests only need to depend on this fixture:

```python
import pytest
from pathlib import Path

from daq_config_server import ConfigClient
from dodal.devices.my_device import MyDevice
from ophyd_async.core import init_devices


@pytest.fixture
def my_device(mock_config_client: ConfigClient) -> MyDevice:
    with init_devices(mock=True):
        return MyDevice(
            config_client=mock_config_client,
            path=Path("tests/test_data/example_lookup_table.json"),
        )
```

### Default file parsing behaviour

The mocked `ConfigClient.get_file_contents()` supports the same return types commonly used by production code:

| Requested type         | Behaviour                                                         |
| ---------------------- | ----------------------------------------------------------------- |
| `str`                  | Returns the raw file contents                                     |
| `dict`                 | Parses the file as JSON and returns a dictionary                  |
| `ConfigModel` subclass | Parses the file as JSON and validates it using `model_validate()` |

For example, if the requested return type is a `ConfigModel` subclass:

```python
config_client.get_file_contents(
    path,
    desired_return_type=MyConfigModel,
)
```

the mock implementation will perform:

```python
MyConfigModel.model_validate(json.loads(contents))
```

### Registering a custom parser

Some configuration file formats are not JSON-based and require custom parsing logic. For these cases, tests can register a parser using `MOCK_CONFIG_CLIENT_PATH_TO_MODEL_CONVERSION`.

This registry maps a file path to a function that converts the file contents into a `ConfigModel`.

For example:

```python
import pytest
from daq_config_server import ConfigClient
from daq_config_server.models.lookup_tables.insertion_device import (
    parse_i09_hu_undulator_energy_gap_lut,
)

from dodal.testing.fixtures.config_client import (
    MOCK_CONFIG_CLIENT_PATH_TO_MODEL_CONVERSION,
)
from tests.devices.beamlines.i09_1_shared.test_data import (
    TEST_HARD_UNDULATOR_LUT,
)


@pytest.fixture
def mock_config_client(mock_config_client: ConfigClient):
    MOCK_CONFIG_CLIENT_PATH_TO_MODEL_CONVERSION[
        TEST_HARD_UNDULATOR_LUT
    ] = parse_i09_hu_undulator_energy_gap_lut

    yield mock_config_client

    MOCK_CONFIG_CLIENT_PATH_TO_MODEL_CONVERSION.pop(
        TEST_HARD_UNDULATOR_LUT,
        None,
    )
```

When `get_file_contents()` is called for `TEST_HARD_UNDULATOR_LUT`, the registered parser will be used instead of the default JSON parsing behaviour.

This mechanism exists as a temporary workaround for configuration formats that are not yet directly supported by daq-config-server.

## Testing beamline module imports and device creation

The tests in `tests/common/beamlines/test_device_instantiation.py` validate that every beamline module can be imported and that all device factories successfully construct devices in a test environment.

During import and device creation, many beamlines load configuration files using either:

* `ConfigClient.get_file_contents()`
* Module-level path constants that point to files on the DLS filesystem

For example:

```python
BEAMLINE_PARAMETERS_PATH = (
    "/dls_sw/i03/software/daq_configuration/json/beamlineParameters.json"
)
```

These files are not available in unit test environments and must not be accessed during tests.

To allow beamline import and device creation tests to run without access to the DLS filesystem, the `module_and_devices_for_beamline` fixture performs two forms of mocking:

1. Replaces `ConfigClient.get_file_contents()` with the `mock_config_client` implementation.
2. Replaces known module-level file path constants with paths to test data files.

### Mocking `ConfigClient`

Before importing the beamline module, the fixture replaces the production implementation:

```python
ConfigClient.get_file_contents = mock_config_client.get_file_contents
```

This ensures that any configuration requested through the daq-config-server client is loaded from local test files rather than the real service.

### Mocking beamline file paths

Some beamlines contain module-level constants that directly reference files on the DLS filesystem. These constants are replaced after module import using the `MOCK_ATTRIBUTES_TABLE`.

For example:

```python
MOCK_ATTRIBUTES_TABLE = {
    "i03": {
        "BEAMLINE_PARAMETERS_PATH": TEST_BEAMLINE_PARAMETERS_TXT,
        "DAQ_CONFIGURATION_PATH": MOCK_DAQ_CONFIG_PATH,
        "ZOOM_PARAMS_FILE": TEST_OAV_ZOOM_LEVELS,
        "DISPLAY_CONFIG": TEST_DISPLAY_CONFIG,
    },
}
```

When the `i03` beamline is tested, these attributes are overwritten with paths to local test files:

```python
mock_beamline_module_filepaths("i03", beamline_module)
```

This allows device factories to load representative configuration data without accessing the real DLS filesystem.

### Adding support for a new beamline

If the device creation tests fail because a beamline attempts to access a file under `/dls` or `/dls_sw`, identify the module attribute containing the path and add an entry to `MOCK_ATTRIBUTES_TABLE`.

For example:

```python
MOCK_ATTRIBUTES_TABLE = { 
    ...
    "iXX: {
        "MY_CONFIGURATION_FILE": TEST_MY_CONFIGURATION_FILE
    },
    ...
}
```

The replacement file should be committed to the test suite and contain the minimum configuration required for the beamline to initialise successfully.

As a rule of thumb:

* Use `mock_config_client` when configuration is loaded through `ConfigClient`.
* Use `MOCK_ATTRIBUTES_TABLE` when a beamline module contains hard-coded filesystem paths.
* If both mechanisms are used by a beamline, both may need to be configured for the tests to pass.



## Test performance and reliability

Dodal has well over 1000 unit tests and developers will run the full unit test suite frequently on their local 
machines, therefore it is imperative that the unit tests are both reliable and run quickly. Ideally the test suite 
should run in about a minute, so if your test takes more than a fraction of a second to complete then consider 
making it faster. The GitHub CI will fail if any test takes longer than 1 second.

Tests that involve concurrency can sometimes be unreliable due to subtle race conditions and variations in timing 
caused by caching, garbage collection and other factors. 
Often these manifest only on certain machines or in CI and are difficult to reproduce. Whilst the odd test failure 
can be worked around by re-running the tests, this is annoying and a build up of such flaky tests is undesirable so 
it is preferable to fix the test.  

### Event loop fuzzer

To assist in the reproduction of concurrency-related test failures, there is an event loop fuzzer available as a 
pytest fixture. The fuzzer introduces random delays into the ``asyncio`` event loop. You can use it as by 
requesting ``event_loop_fuzzing`` as a fixture. It is also recommended when debugging to parametrize the test to 
introduce a good number of iterations in order to ensure the problem has a good chance to show up, but remember to 
remove the parametrization afterwards.

```Python
    import pytest
    # repeat the test a number of times
    @pytest.mark.parametrize("i", range(0, 100))
    async def my_unreliable_test(i, event_loop_fuzzing):
        # Do some stuff in here

```
