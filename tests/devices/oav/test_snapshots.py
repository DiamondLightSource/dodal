from collections.abc import AsyncGenerator
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from aiohttp.client import ClientSession
from aiohttp.test_utils import TestClient, TestServer, unused_port
from aiohttp.web import Response
from aiohttp.web_app import Application
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value
from PIL import Image

from dodal.devices.oav.snapshots.snapshot import (
    Snapshot,
)
from dodal.devices.oav.snapshots.snapshot_with_grid import (
    SnapshotWithGrid,
)


@pytest.fixture
def server_port() -> int:
    return unused_port()


@pytest.fixture
def output_file_name() -> str:
    return f"output-{uuid4()}"


@pytest.fixture
def output_file(tmp_path: Path, output_file_name: str) -> Path:
    return tmp_path / f"{output_file_name}.png"


@pytest.fixture
def image() -> Image.Image:
    return Image.new("RGB", (3, 3))


@pytest.fixture
def image_bytes(image: Image.Image) -> BytesIO:
    buffer = BytesIO()
    image.save(buffer, "png")
    return buffer


@pytest.fixture
async def snapshot(
    tmp_path: Path,
    test_client: TestClient,
    output_file_name: str,
    server_port: int,
) -> AsyncGenerator[Snapshot]:
    def get_session(raise_for_status: bool) -> ClientSession:
        return test_client.session

    with patch(
        "dodal.devices.areadetector.plugins.MJPG.ClientSession", new=get_session
    ):
        async with init_devices(mock=True):
            fake_snapshot = Snapshot("")
        set_mock_value(fake_snapshot.directory, f"{tmp_path}")
        set_mock_value(fake_snapshot.filename, output_file_name)
        set_mock_value(fake_snapshot.url, f"http://127.0.0.1:{server_port}")
        yield fake_snapshot


@pytest.fixture
async def grid_snapshot(
    tmp_path: Path,
    test_client: TestClient,
    output_file_name: str,
    server_port: int,
) -> AsyncGenerator[SnapshotWithGrid]:
    def get_session(raise_for_status: bool) -> ClientSession:
        return test_client.session

    with patch(
        "dodal.devices.areadetector.plugins.MJPG.ClientSession", new=get_session
    ):
        async with init_devices(mock=True):
            fake_grid = SnapshotWithGrid("")

        set_mock_value(fake_grid.top_left_x, 100)
        set_mock_value(fake_grid.top_left_y, 100)
        set_mock_value(fake_grid.box_width, 50)
        set_mock_value(fake_grid.num_boxes_x, 15)
        set_mock_value(fake_grid.num_boxes_y, 10)

        set_mock_value(fake_grid.directory, f"{tmp_path}")
        set_mock_value(fake_grid.filename, output_file_name)
        set_mock_value(fake_grid.url, f"http://127.0.0.1:{server_port}")

        yield fake_grid


@pytest.fixture
async def test_client(
    image_data_coro: AsyncMock, server_port: int
) -> AsyncGenerator[TestClient]:
    app = Application()
    app.router.add_get("", handler=image_data_coro)
    client = TestClient(server=TestServer(app, port=server_port))
    await client.start_server()
    yield client
    await client.close()


@pytest.fixture
def image_data_coro(image_bytes: BytesIO) -> AsyncMock:
    return AsyncMock(return_value=Response(body=image_bytes.getvalue()))


def assert_images_identical(left: Image.Image, right: Image.Image):
    left_data = left.getdata()
    right_data = right.getdata()
    assert len(left_data) == len(right_data)
    for i in range(len(left_data)):
        assert left_data[i] == right_data[i]


async def test_snapshot_correctly_triggered_and_saved(
    snapshot: Snapshot, output_file: Path, image: Image.Image, image_data_coro: Mock
):
    assert not output_file.exists()
    await snapshot.trigger()

    # Get called with an instance of the session and correct url
    image_data_coro.assert_called_once()

    assert await snapshot.last_saved_path.get_value() == f"{output_file}"
    assert output_file.exists()

    with Image.open(output_file) as actual:
        assert_images_identical(actual, image)


async def test_directory_created_when_snapshot_triggered(
    tmp_path: Path,
    snapshot: Snapshot,
    output_file_name: str,
    image: Image.Image,
):
    write_dir = tmp_path / "new_dir"
    assert not write_dir.exists()
    # Set new directory and test that it's created
    set_mock_value(snapshot.directory, f"{write_dir}")
    await snapshot.trigger()
    assert write_dir.exists()
    output_file = write_dir / f"{output_file_name}.png"
    assert await snapshot.last_saved_path.get_value() == f"{output_file}"
    assert output_file.exists()

    with Image.open(output_file) as actual:
        assert_images_identical(actual, image)


@patch(
    "dodal.devices.oav.snapshots.snapshot_with_grid.add_grid_border_overlay_to_image"
)
@patch("dodal.devices.oav.snapshots.snapshot_with_grid.add_grid_overlay_to_image")
async def test_snapshot_with_grid_triggered_saves_image_and_draws_correct_grid(
    patch_add_border: Mock,
    patch_add_grid: Mock,
    output_file: Path,
    tmp_path: Path,
    output_file_name: str,
    grid_snapshot: SnapshotWithGrid,
):
    await grid_snapshot.trigger()

    with Image.open(output_file) as actual:
        patch_add_border.assert_called_once_with(actual, 100, 100, 50, 15, 10)
        patch_add_grid.assert_called_once_with(actual, 100, 100, 50, 15, 10)

    assert (
        await grid_snapshot.last_path_outer.get_value()
        == f"{tmp_path / f'{output_file_name}_outer_overlay.png'}"
    )

    assert (
        await grid_snapshot.last_path_full_overlay.get_value()
        == f"{tmp_path / f'{output_file_name}_grid_overlay.png'}"
    )
