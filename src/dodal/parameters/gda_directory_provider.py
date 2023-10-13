from functools import lru_cache
from typing import Optional

from aiohttp import ClientSession
from ophyd_async.core import DirectoryInfo, DirectoryProvider
from pydantic import BaseModel


class DataCollectionIdentifier(BaseModel):
    collectionId: int


class VisitDirectoryProviderConfig(BaseModel, frozen=True):
    url: str
    beamline: str
    base_path: str


@lru_cache(maxsize=1)
def make_directory_provider(config: VisitDirectoryProviderConfig):
    return VisitDirectoryProvider(config)


class VisitDirectoryProvider(DirectoryProvider):
    """
    Gets information from a remote service to construct the path that detectors should write to,
    and determine how their files should be named.
    """
    _current_collection: Optional[DirectoryInfo]
    _session: ClientSession

    def __init__(self, config: VisitDirectoryProviderConfig):
        self.config = config

    async def update(self):
        """
        Calls the visit service to create a new data collection in the current visit.
        """
        # TODO: After visit service is more feature complete:
        # TODO: Allow selecting visit as part of the request to BlueAPI
        # TODO: Consume visit information from BlueAPI and pass down to this class
        # TODO: Query visit service to get information about visit and data collection
        # TODO: Use AuthN information as part of verification with visit service
        data_collection = await self.connect("/numtracker")
        collection_id = data_collection.collectionId
        path = f"{self.config.base_path}/{collection_id}"
        prefix = f"{self.config.beamline}_{collection_id}"
        self._current_collection = DirectoryInfo(path, prefix)

    def __call__(self) -> DirectoryInfo:
        if self._current_collection:
            return self._current_collection

        raise Exception("No current collection as update() has not been called")

    def _ensure_connected(self) -> ClientSession:
        if self._session is None or self._session.closed:
            self._session = ClientSession(self.config.url)
        return self._session

    async def connect(  # TODO: Generify when required.
            self,
            endpoint: str,
    ) -> DataCollectionIdentifier:
        async with self._ensure_connected() as session:
            async with session.get(endpoint) as response:
                if response.status == 200:
                    json = await response.json()
                    return DataCollectionIdentifier.parse_obj(json)
                else:
                    raise Exception(response.status)
