import os
from typing import TypeVar

from pydantic import BaseModel

TBaseModel = TypeVar("TBaseModel", bound=BaseModel)


def load_json_file_to_class(
    t: type[TBaseModel],
    file: str,
) -> TBaseModel:
    if not os.path.isfile(file):
        raise FileNotFoundError(f"Cannot find file {file}")

    with open(file) as f:
        json_obj = f.read()
    cls = t.model_validate_json(json_obj)
    return cls


def save_class_to_json_file(model: BaseModel, file: str) -> None:
    with open(file, "w") as f:
        f.write(model.model_dump_json())
