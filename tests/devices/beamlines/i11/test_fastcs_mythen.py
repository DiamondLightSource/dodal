import pytest
from ophyd_async.core import (
    PathProvider,
    SignalDict,
    get_mock_put,
    init_devices,
    set_mock_value,
)

from dodal.devices.beamlines.i11.fastcs_mythen import (
    _BIT_DEPTH,
    _DEADTIMES,
    FastCSMythen3,
    FastCSMythen3ArmLogic,
    FastCSMythen3TriggerLogic,
    Mythen3DetectorState,
    Mythen3TriggerMode,
)


@pytest.fixture
async def fastcs_mythen(
    static_path_provider: PathProvider,
) -> FastCSMythen3:
    async with init_devices(mock=True):
        mythen = FastCSMythen3(
            "test_prefix", static_path_provider, name="fastcs_mythen"
        )
    return mythen


def test_fastcs_mythen_deadtime(fastcs_mythen: FastCSMythen3) -> None:
    trigger_logic = FastCSMythen3TriggerLogic(fastcs_mythen.driver)
    assert trigger_logic.get_deadtime(SignalDict()) == _DEADTIMES[_BIT_DEPTH]


async def test_fastcs_mythen_prepare_internal(fastcs_mythen: FastCSMythen3) -> None:
    trigger_logic = FastCSMythen3TriggerLogic(fastcs_mythen.driver)

    await trigger_logic.prepare_internal(num=5, livetime=0.1, deadtime=0.02)

    get_mock_put(fastcs_mythen.driver.trigger_mode).assert_called_once_with(
        Mythen3TriggerMode.TRIGGER
    )
    assert await fastcs_mythen.driver.frames.get_value() == 5
    assert await fastcs_mythen.driver.exposure_time.get_value() == 0.1
    assert await fastcs_mythen.driver.period.get_value() == pytest.approx(0)


async def test_fastcs_mythen_prepare_edge(fastcs_mythen: FastCSMythen3) -> None:
    trigger_logic = FastCSMythen3TriggerLogic(fastcs_mythen.driver)

    await trigger_logic.prepare_edge(num=3, livetime=0.1)

    get_mock_put(fastcs_mythen.driver.trigger_mode).assert_called_once_with(
        Mythen3TriggerMode.TRIGGER
    )
    assert await fastcs_mythen.driver.frames.get_value() == 1
    assert await fastcs_mythen.driver.triggers.get_value() == 3
    assert await fastcs_mythen.driver.exposure_time.get_value() == 0.1


async def test_fastcs_mythen_prepare_level(fastcs_mythen: FastCSMythen3) -> None:
    trigger_logic = FastCSMythen3TriggerLogic(fastcs_mythen.driver)

    await trigger_logic.prepare_level(num=2)

    get_mock_put(fastcs_mythen.driver.trigger_mode).assert_called_once_with(
        Mythen3TriggerMode.TRIGGER_GATING
    )
    assert await fastcs_mythen.driver.frames.get_value() == 2


async def test_fastcs_mythen_data_logic_sets_output_path(
    fastcs_mythen: FastCSMythen3,
    static_path_provider: PathProvider,
) -> None:
    path_info = static_path_provider(fastcs_mythen.name)
    data_logic = fastcs_mythen._data_logics[0]

    await data_logic.prepare_unbounded(fastcs_mythen.name)

    assert await fastcs_mythen.driver.file_path.get_value() == (
        f"{path_info.directory_path}/"
    )
    assert await fastcs_mythen.driver.file_name.get_value() == path_info.filename


async def test_fastcs_mythen_acquire_logic(fastcs_mythen: FastCSMythen3) -> None:
    acquire_logic = FastCSMythen3ArmLogic(fastcs_mythen.driver)
    set_mock_value(fastcs_mythen.driver.frames_written, 0)
    set_mock_value(fastcs_mythen.driver.detector_status, Mythen3DetectorState.IDLE)

    await acquire_logic.start_acquiring()
    await acquire_logic.wait_for_idle()
    assert await fastcs_mythen.driver.acquire.get_value() is True

    await acquire_logic.ensure_stopped()
    assert await fastcs_mythen.driver.stop_acquire.get_value() is True
