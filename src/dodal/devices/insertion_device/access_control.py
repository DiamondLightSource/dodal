import asyncio

from bluesky.protocols import Checkable
from ophyd_async.core import SignalW, StandardReadable, wait_for_value
from ophyd_async.epics.core import epics_signal_r

from dodal.common.enums import EnabledDisabledUpper
from dodal.devices.insertion_device.enum import UndulatorGateStatus


class UndulatorAccessControl(StandardReadable, Checkable[None]):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.gate = epics_signal_r(UndulatorGateStatus, prefix + "BLGATE")
            self.status = epics_signal_r(EnabledDisabledUpper, prefix + "IDBLENA")

        super().__init__(name)

    async def check_value(self, value: None = None):
        status_val, gate_val = await asyncio.gather(
            self.status.get_value(), self.gate.get_value()
        )
        if status_val is EnabledDisabledUpper.DISABLED:
            raise RuntimeError(f"{self.status.name} is DISABLED and cannot move.")
        if gate_val is UndulatorGateStatus.OPEN:
            raise RuntimeError(f"{self.gate.name} is already in motion.")

    async def set_move_and_wait_for_gate(
        self, set_move: SignalW[int], timeout: float | None
    ):
        await set_move.set(1, timeout)
        await wait_for_value(self.gate, UndulatorGateStatus.CLOSE, timeout=timeout)
