from typing import TypeVar

from ophyd_async.core import StrictEnum, SupersetEnum

TAcquisitionMode = TypeVar("TAcquisitionMode", bound=StrictEnum)
# Allow SupersetEnum. Specs analysers can connect to Lens and Psu mode separately to the
# analyser which leaves the enum to either be "Not connected" OR the available enums
# when connected.
TLensMode = TypeVar("TLensMode", bound=SupersetEnum | StrictEnum)
TPsuMode = TypeVar("TPsuMode", bound=SupersetEnum | StrictEnum)
TPassEnergy = TypeVar("TPassEnergy", bound=StrictEnum | float)
TPassEnergyEnum = TypeVar("TPassEnergyEnum", bound=StrictEnum)
