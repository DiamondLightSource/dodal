from os.path import isabs, isfile, join, split
from typing import Generic, Protocol, Self, TypeVar

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


class LoadModelFromFile(Protocol[TBaseModel]):
    def __call__(self, file: str) -> TBaseModel: ...


class LoadModelFromJsonFile(LoadModelFromFile[TBaseModel]):
    def __init__(self, model) -> None:
        self._model = model

    def __call__(self, file: str) -> TBaseModel:
        return load_json_file_to_class(self._model, file)


class ModelLoaderConfig(BaseModel):
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


class ModelLoader(Generic[TBaseModel]):
    """A generic model loader that can be configured with any kind of method to read in
    a file and convert the data into a pydantic model. It can also takes configuration
    to handle the file paths before they are passed to the method to convert to a
    pydantic model.
    """

    def __init__(
        self,
        load_model_from_file: LoadModelFromFile[TBaseModel],
        cfg: ModelLoaderConfig | None = None,
    ):
        self._load_model_from_file = load_model_from_file
        self._cfg = cfg

    def _handle_file_path(self, file: str | None) -> str:
        """Handle the file path based on the configuration provided. If a default path
        is given and a relative file path used, it will join the default path and
        relative path together. If a default file is configured, then you don't need to
        provide a file when using __call__.
        """
        if file is None:
            if self._cfg is None or self._cfg.default_file is None:
                raise RuntimeError(
                    "Model loader has no default file configured and no file was provided."
                )
            file = self._cfg.default_file

        if not isabs(file) and self._cfg is not None:
            file = join(self._cfg.default_path, file)
        return file

    def __call__(self, file: str | None = None) -> TBaseModel:
        """Load a file and return it is as the configured pydantic model.

        Args:
            file (str, optional): The file to load into a pydantic class. If None
            provided, use the default_file from the config.

        Returns:
            An instance of the configurated pydantic base_model type.
        """
        file = self._handle_file_path(file)
        return self._load_model_from_file(file)
