import pytest
from pydantic import BaseModel

from dodal.common.data_util import (
    JsonModelLoader,
    json_model_loader,
    save_class_to_json_file,
)


class MyModel(BaseModel):
    value: str
    number: float


@pytest.fixture
def raw_data() -> dict:
    return {
        "value": "test",
        "number": 3,
    }


@pytest.fixture
def tmp_file(tmp_path, raw_data: dict) -> str:
    path = tmp_path / "json_loader_test.json"
    test_model = MyModel.model_validate(raw_data)
    # Setup tmp file for this test by saving the data.
    save_class_to_json_file(test_model, path)
    return str(path)


@pytest.fixture
def load_json_model_with_default(tmp_file: str) -> JsonModelLoader[MyModel]:
    return json_model_loader(MyModel, tmp_file)


@pytest.fixture
def load_json_model_no_default() -> JsonModelLoader[MyModel]:
    return json_model_loader(MyModel)


def test_json_model_loader_with_default_file(
    load_json_model_with_default: JsonModelLoader[MyModel],
) -> None:
    model = load_json_model_with_default()
    assert model.value == "test"
    assert model.number == 3


def test_json_model_loader_with_file(
    load_json_model_with_default: JsonModelLoader[MyModel], tmp_file: str
) -> None:
    model = load_json_model_with_default(tmp_file)
    assert model.value == "test"
    assert model.number == 3


def test_json_model_loader_with_no_file_or_default_file(
    load_json_model_no_default: JsonModelLoader[MyModel],
) -> None:
    with pytest.raises(
        RuntimeError,
        match="MyModel loader "
        "has no default file configured and no file was provided "
        "when trying to load in a model.",
    ):
        load_json_model_no_default()


def test_json_model_loader_raise_error_if_invalid_file(
    load_json_model_with_default: JsonModelLoader[MyModel],
) -> None:
    with pytest.raises(FileNotFoundError):
        load_json_model_with_default("sdkgsk")
