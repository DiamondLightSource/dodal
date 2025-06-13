from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal

from aiohttp import ClientSession
from ophyd_async.core import FilenameProvider, PathInfo
from pydantic import BaseModel

from dodal.common.types import UpdatingPathProvider
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


class DirectoryServiceClient(ABC):
    """
    Object responsible for I/O in determining collection number
    """

    @abstractmethod
    async def create_new_collection(self) -> DataCollectionIdentifier:
        """Create new collection"""

    @abstractmethod
    async def get_current_collection(self) -> DataCollectionIdentifier:
        """Get current collection"""


class DiamondFilenameProvider(FilenameProvider):
    def __init__(self, beamline: str, client: DirectoryServiceClient):
        self._beamline = beamline
        self._client = client
        self.collectionId: DataCollectionIdentifier | None = None

    def __call__(self, device_name: str | None = None):
        assert device_name, "Diamond filename requires device_name to be passed"
        assert self.collectionId is not None
        return f"{self._beamline}-{self.collectionId.collectionNumber}-{device_name}"


class RemoteDirectoryServiceClient(DirectoryServiceClient):
    """Client for the VisitService REST API
    Currently exposed by the GDA Server to co-ordinate unique filenames.
    While VisitService is embedded in GDA, url is likely to be `ixx-control:8088/api`
    """

    def __init__(self, url: str) -> None:
        self._url = url

    async def create_new_collection(self) -> DataCollectionIdentifier:
        new_collection = await self._identifier_from_response("POST")
        LOGGER.debug("New DataCollection: %s", new_collection)
        return new_collection

    async def get_current_collection(self) -> DataCollectionIdentifier:
        current_collection = await self._identifier_from_response("GET")
        LOGGER.debug("Current DataCollection: %s", current_collection)
        return current_collection

    async def _identifier_from_response(
        self,
        method: Literal["GET", "POST"],
    ) -> DataCollectionIdentifier:
        async with (
            ClientSession() as session,
            session.request(method, f"{self._url}/numtracker") as response,
        ):
            response.raise_for_status()
            json = await response.json()
            return DataCollectionIdentifier.model_validate(json)


class LocalDirectoryServiceClient(DirectoryServiceClient):
    """Local or dummy impl of VisitService client to co-ordinate unique filenames."""

    def __init__(self) -> None:
        self._count = 0

    async def create_new_collection(self) -> DataCollectionIdentifier:
        self._count += 1
        LOGGER.debug("New DataCollection: %s", self._count)
        return DataCollectionIdentifier(collectionNumber=self._count)

    async def get_current_collection(self) -> DataCollectionIdentifier:
        LOGGER.debug("Current DataCollection: %s", self._count)
        return DataCollectionIdentifier(collectionNumber=self._count)


class StaticVisitPathProvider(UpdatingPathProvider):
    """
    Static (single visit) implementation of PathProvider whilst awaiting auth infrastructure to generate necessary information per-scan.
    Allows setting a singular visit into which all run files will be saved.
    update() queries a visit service to get the next DataCollectionIdentifier to increment the suffix of all file writers' next files.
    Requires that all detectors are running with a mutual view on the filesystem.
    Supports a single Visit which should be passed as a Path relative to the root of the Detector IOC mounting.
    i.e. to write to visit /dls/ixx/data/YYYY/cm12345-1
    """

    def __init__(
        self,
        beamline: str,
        root: Path,
        client: DirectoryServiceClient | None = None,
    ):
        self._beamline = beamline
        self._client = client or RemoteDirectoryServiceClient(
            f"{beamline}-control:8088/api"
        )
        self._filename_provider = DiamondFilenameProvider(self._beamline, self._client)
        self._root = root
        self.current_collection: PathInfo | None
        self._session: ClientSession | None

    async def update(self, **kwargs) -> None:
        """
        Creates a new data collection in the current visit.
        """
        # https://github.com/DiamondLightSource/dodal/issues/452
        # TODO: Allow selecting visit as part of a request
        # TODO: DAQ-4827: Pass AuthN information as part of request

        try:
            self._filename_provider.collectionId = (
                await self._client.create_new_collection()
            )
        except Exception:
            LOGGER.error(
                "Exception while updating data collection, preventing overwriting data by setting current_collection to None"
            )
            self._collection_id_info = None
            raise

    async def data_session(self) -> str:
        collection = await self._client.get_current_collection()
        return f"{self._beamline}-{collection.collectionNumber}"

    def __call__(self, device_name: str | None = None) -> PathInfo:
        assert device_name, "Must call PathProvider with device_name"
        return PathInfo(
            directory_path=self._root, filename=self._filename_provider(device_name)
        )
