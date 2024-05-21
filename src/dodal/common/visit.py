from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from aiohttp import ClientSession
from bluesky import RunEngine
from bluesky import plan_stubs as bps
from bluesky import preprocessors as bpp
from bluesky.run_engine import call_in_bluesky_event_loop
from bluesky.utils import make_decorator
from ophyd_async.core import DirectoryInfo, DirectoryProvider
from pydantic import BaseModel

from dodal.beamlines import beamline_utils
from dodal.common.types import MsgGenerator, RunEngineAwareDirectoryProvider
from dodal.log import LOGGER

"""
Functionality required for/from the API of a DirectoryService which exposes the specifics of the Diamond filesystem.
"""

DATA_SESSION = "data_session"
DATA_GROUPS = "data_groups"


class DataCollectionIdentifier(BaseModel):
    """
    Equivalent to a `Scan Number` or `scan_id`, non-globally unique scan identifier.
    Should be always incrementing, unique per-visit, co-ordinated with any other scan engines.
    """

    collectionNumber: int


class ScanNumberProvider(ABC):
    """
    Object responsible for I/O in determining collection number
    """

    @abstractmethod
    async def create_new_collection(self) -> DataCollectionIdentifier:
        """Create new collection"""

    @abstractmethod
    async def get_current_collection(self) -> DataCollectionIdentifier:
        """Get current collection"""


class RemoteScanNumberProvider(ScanNumberProvider):
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


class InMemoryScanNumberProvider(ScanNumberProvider):
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


class VisitDirectory(BaseModel):
    root: Path
    beamline: str


class ScanNumberDirectoryProvider(RunEngineAwareDirectoryProvider):
    """
    DirectoryProvider that integrates with the RunEngine's scan_number hook. Generates a
    scan number using injected logic and applies it to itself and the hook. Detectors
    then write to a location determined by the RunEngine's scan_number, which also
    appears in run metadata.
    """

    _visit_directory: VisitDirectory
    _client: ScanNumberProvider
    _scan_number: int | None

    def __init__(
        self,
        visit_directory: VisitDirectory | None = None,
        client: ScanNumberProvider | None = None,
    ):
        self._visit_directory = visit_directory or VisitDirectory(
            root=Path("/tmp"),
            beamline="unknown-beamline",
        )
        self._client = client or InMemoryScanNumberProvider()
        self._scan_number = None
        super().__init__()

    def next_scan_number(self) -> int:
        """
        Hook to pass to the RunEngine to make sure its scan_number is kept in sync
        with this DirectoryProvider's scan_number. Generates a new scan number
        as a side effect and returns it.

        Returns:
            int: A new scan number for detectors to use.
        """

        collection = call_in_bluesky_event_loop(self._client.create_new_collection())
        self.scan_number = collection.collectionNumber
        return self.scan_number

    def __call__(self) -> DirectoryInfo:
        if self._scan_number is not None:
            return DirectoryInfo(
                # See DocString of DirectoryInfo. At DLS, root = visit directory, resource_dir is relative to it.
                root=self._visit_directory.root,
                # https://github.com/DiamondLightSource/dodal/issues/452
                # Currently all h5 files written to visit/ directory, as no guarantee that visit/dataCollection/ directory will have been produced. If it is as part of #452, append the resource_dir
                resource_dir=Path("."),
                # Diamond standard file naming
                prefix=f"{self._visit_directory.beamline}-{self._scan_number}-",
            )
        else:
            raise ValueError(
                "No current collection, update() needs to be called at least once"
            )
