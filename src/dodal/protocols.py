from abc import abstractmethod
from typing import Generic, Protocol, TypeVar

from ophyd_async.core import Device

DeviceT = TypeVar("DeviceT", bound=Device)


class EnergySource(Protocol, Generic[DeviceT]):
    """Class that directly defines an energy device."""

    energy: DeviceT


DeviceT_CO = TypeVar("DeviceT_CO", bound=Device, covariant=True)


class EnergyWrapper(Protocol, Generic[DeviceT_CO]):
    """Class that indirectly defines an energy device and exposes it via a property."""

    @property
    @abstractmethod
    def energy(self) -> DeviceT_CO:
        """Property or class variable that defines energy in some way."""


"""A class that defines an energy device."""
EnergyDevice = EnergyWrapper[DeviceT] | EnergySource[DeviceT]
