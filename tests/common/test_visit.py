from unittest.mock import AsyncMock, MagicMock, patch

from dodal.common.visit import RemoteDirectoryServiceClient


def create_valid_response(mock_request):
    mock_request.return_value.__aenter__.return_value = (mock_response := MagicMock())
    mock_response.json = AsyncMock(return_value={"collectionNumber": 1})


@patch("dodal.common.visit.ClientSession.request")
async def test_when_create_new_collection_called_on_remote_directory_service_client_then_url_posted_to(
    mock_request: MagicMock,
):
    create_valid_response(mock_request)
    test_url = "test.com"
    client = RemoteDirectoryServiceClient(test_url)
    collection = await client.create_new_collection()
    assert collection.collectionNumber == 1
    mock_request.assert_called_with("POST", f"{test_url}/numtracker")


@patch("dodal.common.visit.ClientSession.request")
async def test_when_get_current_collection_called_on_remote_directory_service_client_then_url_got_from(
    mock_request: MagicMock,
):
    create_valid_response(mock_request)
    test_url = "test.com"
    client = RemoteDirectoryServiceClient(test_url)
    collection = await client.get_current_collection()
    assert collection.collectionNumber == 1
    mock_request.assert_called_with("GET", f"{test_url}/numtracker")
