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
    excitation_energy signal, units eV.
    """

    def __init__(self, name: str = "") -> None:
        self.excitation_energy = self._excitation_energy_signal()
        super().__init__(name)

    @abstractmethod
    def _excitation_energy_signal(self) -> SignalR[float]:
        """
        Signal to provide the excitation energy value in eV.
        """


class EnergySource(AbstractEnergySource):
    """
    Wraps a signal that relates to energy and provides common interface via
    excitation_energy signal. It also provides the name of the wrapped signal in the
    read_configuration via wrapped_device_name.
    """

    def __init__(self, source: SignalR[float], name: str = "") -> None:
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.wrapped_device_name, _ = soft_signal_r_and_setter(
                str, initial_value=source.name
            )
        self.source = Reference(source)
        super().__init__(name)
        self.add_readables([self.excitation_energy])

    def _excitation_energy_signal(self) -> SignalR[float]:
        return derived_signal_r(
            self._get_energy, derived_units="eV", energy=self.source()
        )

    def _get_energy(self, energy: float) -> float:
        return energy


class DualEnergySource(AbstractEnergySource):
    """
    Holds two EnergySource devices and provides a signal to read excitation energy
    depending on which source is selected. This is controlled by a selected_source
    signal which can switch source using SelectedSource enum. Both sources excitation
    energy is recorded in the read, the excitation_energy is used as a helper signal
    to know which source is being used.
    """

    def __init__(self, source1: EnergySource, source2: EnergySource, name: str = ""):
        """
        Args:
            source1: Default EnergySource device to select.
            source2: Secondary EnergySource device to select.
            name: name of this device.
        """
        with self.add_children_as_readables():
            self.selected_source = soft_signal_rw(
                SelectedSource, initial_value=SelectedSource.SOURCE1
            )
            self.source1 = source1
            self.source2 = source2

        super().__init__(name)

    def _excitation_energy_signal(self) -> SignalR[float]:
        return derived_signal_r(
            self.get_selected_source_value,
            derived_units="eV",
            selected_source=self.selected_source,
            source1=self.source1.excitation_energy,
            source2=self.source2.excitation_energy,
        )

    def get_selected_source_value(
        self,
        selected_source: SelectedSource,
        source1: float,
        source2: float,
    ) -> float:
        match selected_source:
            case SelectedSource.SOURCE1:
                return source1
            case SelectedSource.SOURCE2:
                return source2
