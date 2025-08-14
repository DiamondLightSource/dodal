from ophyd_async.core import (
    SignalR,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_r,
    soft_signal_r_and_setter,
    soft_signal_rw,
)

from dodal.devices.electron_analyser.enums import SelectedSource


class SingleEnergySource(StandardReadable):
    """
    Class that provides interface for excitation_energy signal.
    """

    def __init__(self, source: SignalR[float], name: str = "") -> None:
        with self.add_children_as_readables():
            self.excitation_energy = derived_signal_r(
                self._get_excitation_energy, derived_units="eV", value=source
            )
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.source_device, _ = soft_signal_r_and_setter(
                str, initial_value=source.name
            )
        super().__init__(name)

    def _get_excitation_energy(self, value: float) -> float:
        return value


class DualEnergySource(StandardReadable):
    """
    Holds two energy sources and provides signal to read excitation energy depending on
    which source is selected. This is controlled by a selected_source signal which can
    switch to the values of the SelectedSource enum.
    """

    def __init__(
        self, source1: SignalR[float], source2: SignalR[float], name: str = ""
    ):
        """
        Args:
            source1: Default energy source signal that can be read. Units assumed to be
                     eV.
            source2: Secondary excitation energy source that can be read. Units assumed
                     to be eV.
            name: name of this device.
        """
        with self.add_children_as_readables():
            self.selected_source = soft_signal_rw(
                SelectedSource, initial_value=SelectedSource.SOURCE1
            )
            self.excitation_energy = derived_signal_r(
                self.get_selected_source_value,
                derived_units="eV",
                selected_source=self.selected_source,
                source1=source1,
                source2=source2,
            )

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.source1_device, _ = soft_signal_r_and_setter(
                str, initial_value=source1.name
            )
            self.source2_device, _ = soft_signal_r_and_setter(
                str, initial_value=source2.name
            )

        super().__init__(name)

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
