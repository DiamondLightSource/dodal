from ophyd_async.core import YamlSettingsProvider
from ophyd_async.fastcs.panda import HDFPanda
from ophyd_async.plan_stubs import apply_panda_settings, retrieve_settings


def load_panda_from_yaml(yaml_directory: str, yaml_file_name: str, panda: HDFPanda):
    provider = YamlSettingsProvider(yaml_directory)
    settings = yield from retrieve_settings(provider, yaml_file_name, panda)
    yield from apply_panda_settings(settings)
