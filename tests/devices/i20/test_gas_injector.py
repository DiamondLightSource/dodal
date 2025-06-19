from unittest.mock import AsyncMock, call, patch

import pytest

from dodal.devices.i20.gas_injector import (
    GasInjector,
    GasToInject,
    IonChamberToFill,
    PressureMode,
    VacuumPumpCommands,
    ValveCommands,
)


@pytest.fixture
def injector():
    # Patch epics_signal_rw and epics_signal_r to return AsyncMocks
    with (
        patch(
            "dodal.devices.i20.gas_injector.epics_signal_rw",
            side_effect=lambda *a, **k: AsyncMock(),
        ) as _,
        patch(
            "dodal.devices.i20.gas_injector.epics_signal_r",
            side_effect=lambda *a, **k: AsyncMock(),
        ),
    ):
        yield GasInjector("BLXX:")


def test_get_gas_valve_returns_correct_valve(injector):
    for gas in GasToInject:
        valve = injector.get_gas_valve(gas)
        assert isinstance(valve, AsyncMock)


def test_get_chamber_valve_returns_correct_valve(injector):
    for chamber in IonChamberToFill:
        valve = injector.get_chamber_valve(chamber)
        assert isinstance(valve, AsyncMock)


@pytest.mark.asyncio
async def test_inject_gas_sequence(monkeypatch, injector):
    # Patch observe_value to simulate pressure readings
    pressures = [0.0, 0.5, 1.0]

    async def fake_observe_value(signal):
        for p in pressures:
            yield p

    monkeypatch.setattr(
        "dodal.devices.i20.gas_injector.observe_value", fake_observe_value
    )

    # Patch all set methods
    for v in injector.gas_valves.values():
        v.set = AsyncMock()
    for v in injector.chambers.values():
        v.set = AsyncMock()
    injector.pressure_controller_2.setpoint.set = AsyncMock()
    injector.pressure_controller_2.mode.set = AsyncMock()

    chamber = IonChamberToFill.i0
    gas = GasToInject.ARGON
    target_pressure = 1.0

    updates = []
    async for update in injector.inject_gas(target_pressure, chamber, gas):
        updates.append(update)

    # Check that the correct sequence of set calls happened
    gas_valve = injector.get_gas_valve(gas)
    chamber_valve = injector.get_chamber_valve(chamber)
    gas_valve.set.assert_has_calls(
        [
            call(ValveCommands.RESET.value),
            call(ValveCommands.OPEN.value),
            call(ValveCommands.CLOSE.value),
        ]
    )
    chamber_valve.set.assert_called_once_with(ValveCommands.CLOSE.value)
    injector.pressure_controller_2.setpoint.set.assert_called_once_with(target_pressure)
    injector.pressure_controller_2.mode.set.assert_has_calls(
        [
            call(PressureMode.PRESSURE_CONTROL.value),
            call(PressureMode.HOLD.value),
        ]
    )
    assert updates[-1].current == pressures[-1]
    assert updates[-1].target == target_pressure


@pytest.mark.asyncio
async def test_purge_chamber_no_leak(monkeypatch, injector):
    # Patch sleep
    monkeypatch.setattr("dodal.devices.i20.gas_injector.sleep", AsyncMock())

    # Patch observe_value to simulate pressure readings for equilibration
    equil_pressures = [0.5, 0.3, 0.15, 0.05, 0.01, 0.01, 0.01]

    async def fake_observe_value(signal):
        for p in equil_pressures:
            yield p

    monkeypatch.setattr(
        "dodal.devices.i20.gas_injector.observe_value", fake_observe_value
    )

    # Patch all set methods
    for v in injector.chambers.values():
        v.set = AsyncMock()
    injector.vacuum_pump.set = AsyncMock()
    injector.line_valve.set = AsyncMock()
    # Patch readout.read to return base and check pressure
    base = {"value": 1.0}
    check = {"value": 2.0}
    injector.pressure_controller_2.readout.read = AsyncMock(side_effect=[base, check])

    chamber = IonChamberToFill.i1
    await injector.purge_chamber(chamber)

    chamber_valve = injector.get_chamber_valve(chamber)
    chamber_valve.set.assert_has_calls(
        [
            call(ValveCommands.RESET.value),
            call(ValveCommands.OPEN.value),
            call(ValveCommands.CLOSE.value),
            call(ValveCommands.CLOSE.value),
        ]
    )
    injector.line_valve.set.assert_has_calls(
        [
            call(ValveCommands.RESET.value),
            call(ValveCommands.OPEN.value),
            call(ValveCommands.CLOSE.value),
        ]
    )
    injector.vacuum_pump.set.assert_has_calls(
        [
            call(VacuumPumpCommands.ON.value),
            call(VacuumPumpCommands.OFF.value),
        ]
    )


@pytest.mark.asyncio
async def test_purge_chamber_with_leak(monkeypatch, injector, capsys):
    monkeypatch.setattr("dodal.devices.i20.gas_injector.sleep", AsyncMock())

    # Patch observe_value to simulate pressure readings for equilibration
    equil_pressures = [0.5, 0.3, 0.15, 0.05, 0.01, 0.01, 0.01]

    async def fake_observe_value(signal):
        for p in equil_pressures:
            yield p

    monkeypatch.setattr(
        "dodal.devices.i20.gas_injector.observe_value", fake_observe_value
    )

    for v in injector.chambers.values():
        v.set = AsyncMock()
    injector.vacuum_pump.set = AsyncMock()
    injector.line_valve.set = AsyncMock()
    base = {"value": 1.0}
    check = {"value": 5.0}  # >3 difference triggers warning
    injector.pressure_controller_2.readout.read = AsyncMock(side_effect=[base, check])

    chamber = IonChamberToFill.iRef
    await injector.purge_chamber(chamber)
    out = capsys.readouterr().out
    assert "WARNING" in out


@pytest.mark.asyncio
async def test_purge_line_sequence(monkeypatch, injector):
    # Patch observe_value to simulate pressure readings
    pressures = [10.0, 9.0, 8.5]

    async def fake_observe_value(signal):
        for p in pressures:
            yield p

    monkeypatch.setattr(
        "dodal.devices.i20.gas_injector.observe_value", fake_observe_value
    )
    injector.vacuum_pump.set = AsyncMock()
    injector.line_valve.set = AsyncMock()
    injector.pressure_controller_1.readout.read = AsyncMock(
        return_value={"value": 10.0}
    )

    updates = []
    async for update in injector.purge_line():
        updates.append(update)

    injector.vacuum_pump.set.assert_has_calls(
        [
            call(VacuumPumpCommands.ON.value),
            call(VacuumPumpCommands.OFF.value),
        ]
    )
    injector.line_valve.set.assert_has_calls(
        [
            call(ValveCommands.RESET.value),
            call(ValveCommands.OPEN.value),
            call(ValveCommands.CLOSE.value),
        ]
    )
    assert updates[-1].current == pressures[-1]


def test_get_gas_valve_invalid_key_raises(injector):
    with pytest.raises(KeyError):
        injector.get_gas_valve("not_a_gas")  # type: ignore


def test_get_chamber_valve_invalid_key_raises(injector):
    with pytest.raises(KeyError):
        injector.get_chamber_valve("not_a_chamber")  # type: ignore
