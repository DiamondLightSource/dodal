"""Communicate with GDA's visit service to define where detectors should write data."""

import asyncio
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Type, TypeVar

from aiohttp import ClientSession
from ophyd_async.core import DirectoryInfo, DirectoryProvider
from pydantic import BaseModel


class DataCollection(BaseModel):
    visitId: str
    collectionId: int
    data: List[Any]


class VisitDataSchema(BaseModel):
    rootDirectoryPath: str
    processedDirectoryPath: str

class InstrumentVisit(BaseModel):
    visitId: str
    title: str
    instrumentName: str
    data: VisitDataSchema


@lru_cache(maxsize=1)
def make_directory_provider(url: str, visit_id: str):
    return GDADirectoryProvider(url, visit_id)

T = TypeVar("T", bound=BaseModel)

class GDADirectoryProvider(DirectoryProvider):
    _current_collection: Optional[DirectoryInfo]
    url: str
    visit_id: str

    def __init__(self, url: str, visit_id: str) -> None:
        """url to the GDA visit service rest root endpoint"""
        self.url = url
        self.visit_id = visit_id
        
        try:
            asyncio.run(asyncio.wait_for(self.connect("visits", response_type=InstrumentVisit, params={"visitId": self.visit_id}), timeout=15))
        except TimeoutError:
            raise Exception(f"Timeout trying to contact {self.url}/visits. Is GDA running?")


    def __call__(self) -> DirectoryInfo:
        if self._current_collection:
            return self._current_collection

        raise Exception("No current collection as update() has not been called")

    async def update(self) -> None:
        """Create new data collection"""

        collection = await self.connect("collections", DataCollection, "post", {"visitId": self.visit_id})
        self._current_collection = f"{collection.visitId}-{collection.collectionId}"

    # dont need params here...
    async def connect(self, endpoint: str, response_type: Type[T], method="get", params: Optional[Mapping[str, str]] = None, body: Optional[Dict[str, str]] = None) -> T:
        async with ClientSession() as session:
            async with session.request(method=method, url=str(Path(self.url) / endpoint), json=body) as response:
                if response.status == 200:
                    json = await response.json()
                    result = response_type.parse_obj(json)
                else:
                    raise Exception(response.status)
        
        return result

            