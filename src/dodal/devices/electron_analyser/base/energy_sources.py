from abc import abstractmethod

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


class AbstractEnergySource(StandardReadable):
    """
    Abstract device that wraps an energy source signal and provides common interface via
    a energy signal.
    """

    def __init__(self, name: str = "") -> None:
        super().__init__(name)

    @property
    @abstractmethod
    def energy(self) -> SignalR[float]:
        """
        Signal to provide the excitation energy value in eV.
        """


class EnergySource(AbstractEnergySource):
    """
    Wraps a signal that relates to energy and provides common interface via energy
    signal. It provides the name of the wrapped signal as a child signal in the
    read_configuration via wrapped_device_name and adds the signal as a readable.
    """

    def __init__(self, source: SignalR[float], name: str = "") -> None:
        self.add_readables([source])
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.wrapped_device_name, _ = soft_signal_r_and_setter(
                str, initial_value=source.name
            )
        self._source_ref = Reference(source)
        super().__init__(name)

    @property
    def energy(self) -> SignalR[float]:
        return self._source_ref()


def get_float_from_selected_source(
    selected: SelectedSource, s1: float, s2: float
) -> float:
    return get_obj_from_selected_source(selected, s1, s2)


class DualEnergySource(AbstractEnergySource):
    """
    Holds two EnergySource devices and provides a signal to read energy depending on
    which source is selected. This is controlled by a selected_source signal which can
    switch source using SelectedSource enum. Both sources energy is recorded in the
    read, the energy signal is used as a helper signal to know which source is being
    used.
    """

    def __init__(
        self,
        source1: SignalR[float],
        source2: SignalR[float],
        selected_source: SignalRW[SelectedSource],
        name: str = "",
    ):
        """
        Args:
            source1: Default energy signal to select.
            source2: Secondary energy signal to select.
            name: name of this device.
        """

        self.selected_source_ref = Reference(selected_source)
        with self.add_children_as_readables():
            self.source1 = EnergySource(source1)
            self.source2 = EnergySource(source2)

        self._selected_energy = derived_signal_r(
            get_float_from_selected_source,
            "eV",
            selected=self.selected_source_ref(),
            s1=self.source1.energy,
            s2=self.source2.energy,
        )
        super().__init__(name)

    @property
    def energy(self) -> SignalR[float]:
        return self._selected_energy
