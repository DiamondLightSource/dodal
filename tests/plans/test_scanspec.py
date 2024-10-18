from pathlib import Path

import pytest
from bluesky.run_engine import RunEngine
from event_model.documents import (
    DocumentType,
)
from ophyd_async.core import (
    DeviceCollector,
    PathProvider,
    callback_on_mock_put,
    set_mock_value,
)
from ophyd_async.epics.adaravis import AravisDetector
from ophyd_async.epics.motor import Motor
from scanspec.specs import Line, Spiral

from dodal.common.beamlines.beamline_utils import set_path_provider
from dodal.common.visit import StaticVisitPathProvider
from dodal.plans import spec_scan


@pytest.fixture
def x_axis(RE: RunEngine) -> Motor:
    with DeviceCollector(mock=True):
        x_axis = Motor("DUMMY:X:")
    set_mock_value(x_axis.velocity, 1)
    return x_axis


@pytest.fixture
def y_axis(RE: RunEngine) -> Motor:
    with DeviceCollector(mock=True):
        y_axis = Motor("DUMMY:X:")
    set_mock_value(y_axis.velocity, 1)
    return y_axis


@pytest.fixture
def path_provider(static_path_provider: PathProvider):
    assert isinstance(static_path_provider, StaticVisitPathProvider)
    set_path_provider(static_path_provider)
    yield static_path_provider
    set_path_provider(None)  # type: ignore


@pytest.fixture
def det(RE: RunEngine, path_provider: PathProvider, tmp_path: Path) -> AravisDetector:
    with DeviceCollector(mock=True):
        det = AravisDetector("DUMMY:DET", path_provider=path_provider)

    def ready_to_write(file_name: str, *_, **__):
        set_mock_value(det.hdf.file_path_exists, True)
        set_mock_value(det.hdf.full_file_name, str(tmp_path / f"{file_name}.h5"))

    callback_on_mock_put(det.hdf.file_path, ready_to_write)
    set_mock_value(det.hdf.capture, True)

    return det


def test_metadata_of_simple_spec(RE: RunEngine, x_axis: Motor, det: AravisDetector):
    spec = Line(axis=x_axis, start=1, stop=2, num=3)

    docs: list[tuple[str, DocumentType]] = []

    def capture_doc(name: str, doc: DocumentType):
        docs.append((name, doc))

    RE(spec_scan({det}, spec), capture_doc)

    # Start, Descriptor, StreamResource, StreamDatum, Event * 3, Stop
    assert len(docs) == 8


def test_metadata_of_spiral_spec(
    RE: RunEngine, x_axis: Motor, y_axis: Motor, det: AravisDetector
):
    spec = Spiral.spaced(x_axis, y_axis, 0, 0, 5, 1)
    docs: list[tuple[str, DocumentType]] = []

    def capture_doc(name: str, doc: DocumentType):
        docs.append((name, doc))

    RE(spec_scan({det}, spec), capture_doc)
