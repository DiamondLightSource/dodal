from typing import Any, TypedDict

import numpy as np
from numpy.typing import NDArray
from ophyd_async.core import StandardReadable

from dodal.devices.ophyd_async_utils import create_soft_signal_r

SORT_KEY = "max_count"


class XrcResult(TypedDict):
    centre_of_mass: list[int]
    max_voxel: list[int]
    max_count: int
    n_voxels: int
    total_count: int
    bounding_box: list[list[int]]


def parse_reading(reading: dict[str, Any], name: str = "zocalo_results") -> XrcResult:
    return {
        "centre_of_mass": list(reading[f"{name}-centre_of_mass"]["value"]),
        "max_voxel": list(reading[f"{name}-max_voxel"]["value"]),
        "max_count": reading[f"{name}-max_count"]["value"],
        "n_voxels": reading[f"{name}-n_voxels"]["value"],
        "total_count": reading[f"{name}-total_count"]["value"],
        "bounding_box": [list(p) for p in reading[f"{name}-bounding_box"]["value"]],
    }


class ZocaloResults(StandardReadable):
    """An ophyd device which can wait for results from a Zocalo job"""

    def __init__(self, name: str = "zocalo_results", sort_key: str = SORT_KEY) -> None:
        self.centre_of_mass = create_soft_signal_r(
            NDArray[np.uint], "centre_of_mass", self.name
        )
        self.max_voxel = create_soft_signal_r(NDArray[np.uint], "max_voxel", self.name)
        self.max_count = create_soft_signal_r(int, "max_count", self.name)
        self.n_voxels = create_soft_signal_r(int, "n_voxels", self.name)
        self.total_count = create_soft_signal_r(int, "total_count", self.name)
        self.bounding_box = create_soft_signal_r(
            NDArray[np.uint], "bounding_box", self.name
        )
        self.set_readable_signals(
            read=[
                self.centre_of_mass,
                self.max_voxel,
                self.max_count,
                self.n_voxels,
                self.total_count,
                self.bounding_box,
            ]
        )
        super().__init__(name)

    async def _put_result(self, result: XrcResult):
        await self.centre_of_mass._backend.put(np.array(result["centre_of_mass"]))
        await self.max_voxel._backend.put(np.array(result["max_voxel"]))
        await self.max_count._backend.put(result["max_count"])
        await self.n_voxels._backend.put(result["n_voxels"])
        await self.total_count._backend.put(result["total_count"])
        await self.bounding_box._backend.put(np.array(result["bounding_box"]))


"""
results have the format:
"results": [
                    {
                        "centre_of_mass": [1, 2, 3],
                        "max_voxel": [2, 4, 5],
                        "max_count": 105062,
                        "n_voxels": 35,
                        "total_count": 2387574,
                        "bounding_box": [[1, 2, 3], [3, 4, 4]],
                    },
                    ...
                ]
these are broken into
centre_of_mass 2darray
max voxel 2darray
max count
n_voxels
total_count
bounding box 3darray
sorted by
"""
