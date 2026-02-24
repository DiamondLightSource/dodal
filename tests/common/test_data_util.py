from os.path import split

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
def raw_data_default_file() -> dict:
    return {
        "value": "test1",
        "number": 0,
    }


@pytest.fixture
def raw_data_tmp_file() -> dict:
    return {
        "value": "test2",
        "number": 3,
    }


@pytest.fixture
def default_tmp_file(tmp_path, raw_data_default_file: dict) -> str:
    path = tmp_path / "json_loader_default_file.json"
    test_model = MyModel.model_validate(raw_data_default_file)
    # Setup tmp file for this test by saving the data.
    save_class_to_json_file(test_model, path)
    return str(path)


@pytest.fixture
def tmp_file(tmp_path, raw_data_tmp_file: dict) -> str:
    path = tmp_path / "json_loader_file.json"
    test_model = MyModel.model_validate(raw_data_tmp_file)
    # Setup tmp file for this test by saving the data.
    save_class_to_json_file(test_model, path)
    return str(path)


@pytest.fixture
def load_json_model_with_default(default_tmp_file: str) -> JsonModelLoader[MyModel]:
    return json_model_loader(MyModel, default_tmp_file)


@pytest.fixture
def load_json_model_no_default() -> JsonModelLoader[MyModel]:
    return json_model_loader(MyModel)


def test_json_model_loader_with_default_file(
    load_json_model_with_default: JsonModelLoader[MyModel],
) -> None:
    model = load_json_model_with_default()
    assert model.value == "test1"
    assert model.number == 0


def test_json_model_loader_with_abs_file_path(
    load_json_model_with_default: JsonModelLoader[MyModel], tmp_file: str
) -> None:
    model = load_json_model_with_default(tmp_file)
    assert model.value == "test2"
    assert model.number == 3


def test_json_model_loader_with_relative_file_path(
    load_json_model_with_default: JsonModelLoader[MyModel], tmp_file: str
) -> None:
    path, file = split(tmp_file)
    model = load_json_model_with_default(file)
    assert model.value == "test2"
    assert model.number == 3


def test_json_model_loader_with_no_file_or_default_file(
    load_json_model_no_default: JsonModelLoader[MyModel],
) -> None:
    with pytest.raises(
        RuntimeError,
        match="MyModel loader has no default file configured and no file was provided "
        "when trying to load in a model.",
    ):
        load_json_model_no_default()


def test_json_model_loader_raise_error_if_invalid_file(
    load_json_model_with_default: JsonModelLoader[MyModel],
) -> None:
    with pytest.raises(FileNotFoundError):
        load_json_model_with_default("sdkgsk")
