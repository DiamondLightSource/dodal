from os.path import isabs, isfile, join, split
from typing import Protocol, Self, TypeVar

from pydantic import BaseModel

TBaseModel = TypeVar("TBaseModel", bound=BaseModel, covariant=True)


def load_json_file_to_class(t: type[TBaseModel], file: str) -> TBaseModel:
    """Load json file into a pydantic model class.

    Args:
        t (type[TBaseModel]): type of model to load a file into to.
        file (str): The file to read.

    Returns:
        An instance of pydantic BaseModel.
    """
    if not isfile(file):
        raise FileNotFoundError(f"Cannot find file {file}")

    with open(file) as f:
        json_obj = f.read()
    cls = t.model_validate_json(json_obj)
    return cls


def save_class_to_json_file(model: BaseModel, file: str) -> None:
    """Save a pydantic model as a json file.

    Args:
        model (BaseModel): The pydantic model to save to json file.
        file (str): The file path to save the model to.
    """
    with open(file, "w") as f:
        f.write(model.model_dump_json())


class JsonModelLoader(Protocol[TBaseModel]):
    def __call__(self, file: str | None = None) -> TBaseModel: ...


class JsonLoaderConfig(BaseModel):
    default_path: str
    default_file: str | None

    @classmethod
    def from_default_file(cls, default_file: str) -> Self:
        """Create instance by splitting path from file to set defaults."""
        default_path, default_file = split(default_file)
        return cls(default_path=default_path, default_file=default_file)

    @classmethod
    def from_default_path(cls, default_path: str) -> Self:
        """Create instance by only setting a default path."""
        return cls(default_path=default_path, default_file=None)

    def update_config_from_file(self, new_file: str) -> None:
        """Update exisiting config by splitting path from file to set new defaults."""
        self.default_path, self.default_file = split(new_file)


def json_model_loader(
    model: type[TBaseModel], config: JsonLoaderConfig | None = None
) -> JsonModelLoader[TBaseModel]:
    """Factory to create a function that loads a json file into a configured pydantic
    model and with optional configuration for default path and file to use.
    """

    def load_json(file: str | None = None) -> TBaseModel:
        """Load a json file and return it is as the configured pydantic model.

        Args:
            file (str, optional): The file to load into a pydantic class. If None
            provided, use the default_file from the config.

        Returns:
            An instance of the configurated pydantic base_model type.
        """
        if file is None:
            if config is None or config.default_file is None:
                raise RuntimeError(
                    f"{model.__name__} loader has no default file configured "
                    "and no file was provided."
                )
            file = config.default_file

        if not isabs(file) and config is not None:
            file = join(config.default_path, file)
        return load_json_file_to_class(model, file)

    return load_json
