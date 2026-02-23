import os
from typing import Generic, TypeVar

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


class JsonModelLoader(Generic[TBaseModel]):
    def __init__(
        self, base_model: type[TBaseModel], default_file: str | None = None
    ) -> None:
        self._base_model = base_model
        self.default_file = default_file

    def __call__(self, file: str | None = None) -> TBaseModel:
        if file is None and self.default_file is not None:
            return load_json_file_to_class(self._base_model, self.default_file)
        elif file is not None:
            return load_json_file_to_class(self._base_model, file)
        raise TypeError("JsonLoader has no default file configured.")
