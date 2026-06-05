from ophyd_async.core import (
    Reference,
    SignalR,
    SignalRW,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_r,
    soft_signal_r_and_setter,
)

from dodal.devices.selectable_source import SelectedSource, get_obj_from_selected_source


def get_float_from_selected_source(
    selected: SelectedSource, s1: float, s2: float
) -> float:
    """Wrapper function to provide type hints for derived signal."""
    return get_obj_from_selected_source(selected, s1, s2)


class DualEnergySource(StandardReadable):
    """Provides a signal to read energy depending on
    which source is selected. The energy is the one that corrosponds to the
    selected_source signal. For example, selected_source is source1 if selected_source
    is at SelectedSource.SOURCE1 and vise versa for source2 and
    SelectedSource.SOURCE2.

    Args:
        source1 (SignalR): Energy source that corrosponds to SelectedSource.SOURCE1.
        source2 (SignalR): Energy source that corrosponds to SelectedSource.SOURCE2.
        selected_source (SignalRW): Signal that decides the active energy source.
        name (str, optional): Name of this device.
    """

    def __init__(
        self,
        source1: SignalR[float],
        source2: SignalR[float],
        selected_source: SignalRW[SelectedSource],
        name: str = "",
    ):
        self.selected_source_ref = Reference(selected_source)
        self.source1_ref = Reference(source1)
        self.source2_ref = Reference(source2)
        with self.add_children_as_readables():
            self.energy = derived_signal_r(
                get_float_from_selected_source,
                "eV",
                selected=selected_source,
                s1=source1,
                s2=source2,
            )

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.source1, _ = soft_signal_r_and_setter(str, initial_value=source1.name)
            self.source2, _ = soft_signal_r_and_setter(str, initial_value=source2.name)
        self.add_readables([selected_source, source1, source2])

        super().__init__(name)
