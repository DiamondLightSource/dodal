import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from aiohttp import ClientSession
from ophyd_async.core import DirectoryInfo, DirectoryProvider, StaticDirectoryProvider
from pydantic import BaseModel

from dodal.log import LOGGER


class DataCollectionIdentifier(BaseModel):
    collectionNumber: int


class VisitServiceClientBase(ABC):
    """
    Object responsible for I/O in determining collection number
    """

    @abstractmethod
    async def create_new_collection(self) -> DataCollectionIdentifier:
        ...

    @abstractmethod
    async def get_current_collection(self) -> DataCollectionIdentifier:
        ...


class VisitServiceClient(VisitServiceClientBase):
    _url: str

    def __init__(self, url: str) -> None:
        self._url = url

    async def create_new_collection(self) -> DataCollectionIdentifier:
        async with ClientSession() as session:
            async with session.post(f"{self._url}/numtracker") as response:
                if response.status == 200:
                    json = await response.json()
                    return DataCollectionIdentifier.parse_obj(json)
                else:
                    raise Exception(response.status)

    async def get_current_collection(self) -> DataCollectionIdentifier:
        async with ClientSession() as session:
            async with session.get(f"{self._url}/numtracker") as response:
                if response.status == 200:
                    json = await response.json()
                    return DataCollectionIdentifier.parse_obj(json)
                else:
                    raise Exception(response.status)


class LocalVisitServiceClient(VisitServiceClientBase):
    _count: int

    def __init__(self) -> None:
        self._count = 0

    async def create_new_collection(self) -> DataCollectionIdentifier:
        count = self._count
        self._count += 1
        return DataCollectionIdentifier(collectionNumber=count)

    async def get_current_collection(self) -> DataCollectionIdentifier:
        return DataCollectionIdentifier(collectionNumber=self._count)


class VisitDirectoryProvider(DirectoryProvider):
    """
    Gets information from a remote service to construct the path that detectors should write to,
    and determine how their files should be named.
    """

    _data_group_name: str
    _data_directory: Path

    _client: VisitServiceClientBase
    _current_collection: Optional[DirectoryInfo]
    _session: Optional[ClientSession]

    def __init__(
        self,
        data_group_name: str,
        data_directory: Path,
        client: VisitServiceClientBase,
    ):
        self._data_group_name = data_group_name
        self._data_directory = data_directory
        self._client = client

        self._current_collection = None
        self._session = None

    async def update(self) -> None:
        """
        Calls the visit service to create a new data collection in the current visit.
        """
        # TODO: After visit service is more feature complete:
        # TODO: Allow selecting visit as part of the request to BlueAPI
        # TODO: Consume visit information from BlueAPI and pass down to this class
        # TODO: Query visit service to get information about visit and data collection
        # TODO: Use AuthN information as part of verification with visit service

        try:
            collection_id_info = await self._client.create_new_collection()
            self._current_collection = self._generate_directory_info(collection_id_info)
        except Exception as ex:
            # TODO: The catch all is needed because the RunEngine will not
            # currently handle it, see
            # https://github.com/bluesky/bluesky/pull/1623
            self._current_collection = None
            LOGGER.exception(ex)

    def _generate_directory_info(
        self,
        collection_id_info: DataCollectionIdentifier,
    ) -> DirectoryInfo:
        collection_id = collection_id_info.collectionNumber
        file_prefix = f"{self._data_group_name}-{collection_id}"
        return DirectoryInfo(str(self._data_directory), file_prefix)

    def __call__(self) -> DirectoryInfo:
        if self._current_collection is not None:
            return self._current_collection
        else:
            raise ValueError(
                "No current collection, update() needs to be called at least once"
            )


_SINGLETON: Optional[VisitDirectoryProvider] = None


def set_directory_provider_singleton(provider: VisitDirectoryProvider):
    global _SINGLETON

    _SINGLETON = provider


def get_directory_provider() -> DirectoryProvider:
    if _SINGLETON is not None:
        return _SINGLETON
    else:
        return StaticDirectoryProvider(tempfile.TemporaryFile(), "")
