from abc import abstractmethod

from ophyd_async.core import (
    Reference,
    SignalR,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_r,
    soft_signal_r_and_setter,
    soft_signal_rw,
)

from dodal.devices.electron_analyser.enums import SelectedSource


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


class DualEnergySource(AbstractEnergySource):
    """
    Holds two EnergySource devices and provides a signal to read energy depending on
    which source is selected. This is controlled by a selected_source signal which can
    switch source using SelectedSource enum. Both sources energy is recorded in the
    read, the energy signal is used as a helper signal to know which source is being
    used.
    """

    def __init__(
        self, source1: SignalR[float], source2: SignalR[float], name: str = ""
    ):
        """
        Args:
            source1: Default energy signal to select.
            source2: Secondary energy signal to select.
            name: name of this device.
        """

        with self.add_children_as_readables():
            self.selected_source = soft_signal_rw(
                SelectedSource, initial_value=SelectedSource.SOURCE1
            )
            self.source1 = EnergySource(source1)
            self.source2 = EnergySource(source2)

        self._selected_energy = derived_signal_r(
            self._get_excitation_energy,
            "eV",
            selected_source=self.selected_source,
            source1=self.source1.energy,
            source2=self.source2.energy,
        )

        super().__init__(name)

    def _get_excitation_energy(
        self, selected_source: SelectedSource, source1: float, source2: float
    ) -> float:
        match selected_source:
            case SelectedSource.SOURCE1:
                return source1
            case SelectedSource.SOURCE2:
                return source2

    @property
    def energy(self) -> SignalR[float]:
        return self._selected_energy
