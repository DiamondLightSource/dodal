from collections.abc import Callable

try:
    from typing import TypeAlias
except ImportError:
    from typing import TypeAlias
from ophyd.device import Device as OphydV1Device
from ophyd_async.core import Device as OphydV2Device

AnyDevice: TypeAlias = OphydV1Device | OphydV2Device
V1DeviceFactory: TypeAlias = Callable[..., OphydV1Device]
V2DeviceFactory: TypeAlias = Callable[..., OphydV2Device]
AnyDeviceFactory: TypeAlias = V1DeviceFactory | V2DeviceFactory
