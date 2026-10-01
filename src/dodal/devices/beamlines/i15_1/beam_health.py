from ophyd_async.core import StandardReadable, StandardReadableFormat, derived_signal_r
from ophyd_async.epics.core import epics_signal_r


class BeamHealth(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self._healthy = epics_signal_r(float, prefix + "PY:Double3_RBV")

        with self.add_children_as_readables():
            self.healthy = derived_signal_r(
                self._is_healthy,
                beam_healthy=self._healthy,
                derived_datatype=bool,
            )
        super().__init__(name)

    def _is_healthy(self, beam_healthy: float) -> bool:
        return bool(beam_healthy)
