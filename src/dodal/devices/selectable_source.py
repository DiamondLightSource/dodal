from typing import TypeVar

from ophyd_async.core import (
    NotConnectedError,
    SignalR,
    SignalRW,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    derived_signal_r,
    soft_signal_r_and_setter,
)


class SelectedSource(StrictEnum):
    SOURCE1 = "source1"
    SOURCE2 = "source2"


T = TypeVar("T")


def get_obj_from_selected_source(selected_source: SelectedSource, s1: T, s2: T) -> T:
    """Util function that maps enum values for SelectedSource to two objects. It then
    returns one of the objects that corrosponds to the selected_source value.
    """
    match selected_source:
        case SelectedSource.SOURCE1:
            return s1
        case SelectedSource.SOURCE2:
            return s2


class DualEnergySource(StandardReadable):
    """Provides a signal to read energy depending on
    which source is selected. The energy is the one that corrosponds to the
    selected_source signal. For example, selected_source is source1 if selected_source
    is at SelectedSource.SOURCE1 and vise versa for source2 and
    SelectedSource.SOURCE2.

    Args:
        source1 (SignalRW): Energy source that corrosponds to SelectedSource.SOURCE1.
        source2 (SignalRW): Energy source that corrosponds to SelectedSource.SOURCE2.
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
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.energy = derived_signal_r(
                self._energy_from_selected_source,
                "eV",
                selected_source=selected_source,
                s1=source1,
                s2=source2,
            )

        self._validate_config_signal([source1, source2])
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.source1, _ = soft_signal_r_and_setter(str, initial_value=source1.name)
            self.source2, _ = soft_signal_r_and_setter(str, initial_value=source2.name)
        self.add_readables([selected_source, source1, source2])

        super().__init__(name)

    def _energy_from_selected_source(
        self, selected_source: SelectedSource, s1: float, s2: float
    ) -> float:
        return get_obj_from_selected_source(selected_source, s1, s2)

    def _validate_config_signal(self, signals: list[SignalR]) -> None:
        for signal in signals:
            if signal.name == "":
                raise NotConnectedError(
                    'Signal cannot have name "". Make sure the signal has been '
                    f"connected and named before passing to class {self.__class__.__name__}"
                )
