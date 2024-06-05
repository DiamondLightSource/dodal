from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from aiohttp import ClientSession
from ophyd_async.core import DirectoryInfo
from pydantic import BaseModel

from dodal.common.types import UpdatingDirectoryProvider
from dodal.log import LOGGER

"""
Functionality required for/from the API of a DirectoryService which exposes the specifics of the Diamond filesystem.
"""


class DataCollectionIdentifier(BaseModel):
    """
    Equivalent to a `Scan Number` or `scan_id`, non-globally unique scan identifier.
    Should be always incrementing, unique per-visit, co-ordinated with any other scan engines.
    """

    collectionNumber: int


class DirectoryServiceClientBase(ABC):
    """
    Object responsible for I/O in determining collection number
    """

    @abstractmethod
    async def create_new_collection(self) -> DataCollectionIdentifier:
        """Create new collection"""

    @abstractmethod
    async def get_current_collection(self) -> DataCollectionIdentifier:
        """Get current collection"""


class DirectoryServiceClient(DirectoryServiceClientBase):
    """Client for the VisitService REST API
    Currently exposed by the GDA Server to co-ordinate unique filenames.
    While VisitService is embedded in GDA, url is likely to be `ixx-control:8088/api`
    """

    _url: str

    def __init__(self, url: str) -> None:
        self._url = url

    async def create_new_collection(self) -> DataCollectionIdentifier:
        async with ClientSession() as session:
            async with session.post(f"{self._url}/numtracker") as response:
                response.raise_for_status()
                json = await response.json()
                new_collection = DataCollectionIdentifier.parse_obj(json)
                LOGGER.debug("New DataCollection: %s", new_collection)
                return new_collection

    async def get_current_collection(self) -> DataCollectionIdentifier:
        async with ClientSession() as session:
            async with session.get(f"{self._url}/numtracker") as response:
                response.raise_for_status()
                json = await response.json()
                current_collection = DataCollectionIdentifier.parse_obj(json)
                LOGGER.debug("Current DataCollection: %s", current_collection)
                return current_collection


class LocalDirectoryServiceClient(DirectoryServiceClientBase):
    """Local or dummy impl of VisitService client to co-ordinate unique filenames."""

    _count: int

    def __init__(self) -> None:
        self._count = 0

    async def create_new_collection(self) -> DataCollectionIdentifier:
        self._count += 1
        LOGGER.debug("New DataCollection: %s", self._count)
        return DataCollectionIdentifier(collectionNumber=self._count)

    async def get_current_collection(self) -> DataCollectionIdentifier:
        LOGGER.debug("Current DataCollection: %s", self._count)
        return DataCollectionIdentifier(collectionNumber=self._count)


class StaticVisitDirectoryProvider(UpdatingDirectoryProvider):
    """
    Static (single visit) implementation of DirectoryProvider whilst awaiting auth infrastructure to generate necessary information per-scan.
    Allows setting a singular visit into which all run files will be saved.
    update() queries a visit service to get the next DataCollectionIdentifier to increment the suffix of all file writers' next files.
    Requires that all detectors are running with a mutual view on the filesystem.
    Supports a single Visit which should be passed as a Path relative to the root of the Detector IOC mounting.
    i.e. to write to visit /dls/ixx/data/YYYY/cm12345-1, assuming all detectors are mounted with /data -> /dls/ixx/data, root=/data/YYYY/cm12345-1/
    """

    _beamline: str
    _root: Path
    _client: DirectoryServiceClientBase
    _current_collection: DirectoryInfo | None
    _session: ClientSession | None

    def __init__(
        self,
        beamline: str,
        root: Path,
        client: Optional[DirectoryServiceClientBase] = None,
    ):
        self._beamline = beamline
        self._client = client or DirectoryServiceClient(f"{beamline}-control:8088/api")
        self._root = root
        self._current_collection = None
        self._session = None

    async def update(self) -> None:
        """
        Creates a new data collection in the current visit.
        """
        # https://github.com/DiamondLightSource/dodal/issues/452
        # TODO: Allow selecting visit as part of a request
        # TODO: DAQ-4827: Pass AuthN information as part of request

        try:
            collection_id_info = await self._client.create_new_collection()
            self._current_collection = self._generate_directory_info(collection_id_info)
        except Exception:
            LOGGER.error(
                "Exception while updating data collection, preventing overwriting data by setting current_collection to None"
            )
            self._current_collection = None
            raise

    def _generate_directory_info(
        self,
        collection_id_info: DataCollectionIdentifier,
    ) -> DirectoryInfo:
        return DirectoryInfo(
            # See DocString of DirectoryInfo. At DLS, root = visit directory, resource_dir is relative to it.
            root=self._root,
            # https://github.com/DiamondLightSource/dodal/issues/452
            # Currently all h5 files written to visit/ directory, as no guarantee that visit/dataCollection/ directory will have been produced. If it is as part of #452, append the resource_dir
            resource_dir=Path("."),
            # Diamond standard file naming
            prefix=f"{self._beamline}-{collection_id_info.collectionNumber}-",
        )

    def __call__(self) -> DirectoryInfo:
        if self._current_collection is not None:
            return self._current_collection
        else:
            raise ValueError(
                "No current collection, update() needs to be called at least once"
            )
