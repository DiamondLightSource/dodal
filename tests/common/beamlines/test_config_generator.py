from dodal.common.beamlines.config_generator import (
    beamline_config_generator,
    translate_beamline_py_config_to_yaml,
)


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


def test_reverse_translate_beamline_py_config_to_yaml(tmp_path):
    py_file = tmp_path / "i10.py"
    py_file.write_text("""
from dodal.devices.custom import CustomDevice

@devices.factory()
def my_device() -> CustomDevice:
    return CustomDevice()
""")

    output_dir = tmp_path / "recovered"
    translate_beamline_py_config_to_yaml(str(py_file), str(output_dir))

    import yaml

    with open(output_dir / "devices.yaml") as f:
        recovered = yaml.safe_load(f)

    assert recovered[0]["device"] == "my_device"
    assert recovered[0]["import_from"] == "dodal.devices.custom"
