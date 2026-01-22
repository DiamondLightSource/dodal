import pytest
import yaml

from dodal.common.beamlines.config_generator import (
    beamline_config_generator,
    translate_beamline_py_config_to_yaml,
)


@pytest.fixture
def mock_config_dir(tmp_path):
    config_dir = tmp_path / "i10"
    config_dir.mkdir()

    config_data = {
        "beamline": "i10",
        "base_imports": ["import os"],
        "setup_script": "PREFIX = '{beamline}'",
        "device_files": ["devices.yaml"],
        "note": "Test Beamline",
    }

    with open(config_dir / "config.yaml", "w") as f:
        yaml.dump(config_data, f)

    return config_dir


def test_generator_output_contains_expected_code(tmp_path):
    # Setup temporary YAML files
    conf_dir = tmp_path / "i10"
    conf_dir.mkdir()

    config_yaml = conf_dir / "config.yaml"
    config_yaml.write_text("""
beamline: i10
output_file: i10.py
base_imports: ["import os"]
setup_script: "PREFIX = '{beamline}'"
device_files: ["devices.yaml"]
""")

    devices_yaml = conf_dir / "devices.yaml"
    devices_yaml.write_text("""
- device: my_motor
  type: MotorClass
  import_from: dodal.devices
  params:
    prefix: 'f"{PREFIX}-MOT-01"'
""")

    code = beamline_config_generator(str(conf_dir))

    assert "def my_motor() -> MotorClass:" in code
    assert "from dodal.devices import MotorClass" in code
    assert 'prefix=f"{PREFIX}-MOT-01"' in code


def test_decorators_with_args(tmp_path, mock_config_dir):
    # YAML representation
    devices_file = mock_config_dir / "devices.yaml"
    devices_file.write_text("""
- device: fancy_motor
  type: Motor
  import_from: dodal.devices
  decorators:
    - name: "devices.factory"
      args:
        skip: True
        reason: "Testing"
    - name: "other.wrapper"
      args:
        priority: 10
""")

    code = beamline_config_generator(str(mock_config_dir))

    assert "@devices.factory(skip=True, reason='Testing')" in code
    assert "@other.wrapper(priority=10)" in code


def test_reverse_translator_recovers_decorator_args(tmp_path):
    py_file = tmp_path / "i10.py"
    py_file.write_text("""
@devices.factory(skip=False)
def my_dev() -> Motor:
    return Motor()
""")
    output_dir = tmp_path / "recovered"
    translate_beamline_py_config_to_yaml(str(py_file), str(output_dir))

    with open(output_dir / "devices.yaml") as f:
        devs = yaml.safe_load(f)
        assert devs[0]["decorators"][0]["name"] == "devices.factory"
        assert devs[0]["decorators"][0]["args"]["skip"] is False
