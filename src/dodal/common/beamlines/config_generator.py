import glob
import os
import subprocess
from collections import defaultdict

import yaml


def format_value(v):
    if isinstance(v, str):
        if "(" in v or ")." in v or v.startswith("PREFIX"):
            return v
        return f"'{v}'"
    return repr(v)


def generate_beamline_code(device_dir):
    sections = defaultdict(list)
    needed_imports = defaultdict(set)

    yaml_files = glob.glob(os.path.join(device_dir, "*.yaml"))

    for y_file in yaml_files:
        with open(y_file) as f:
            content = yaml.safe_load(f)
            device_list = content if isinstance(content, list) else [content]

            for dev in device_list:
                sections[dev.get("section", "Other")].append(dev)
                if dev.get("import_from") and dev.get("type"):
                    needed_imports[dev["import_from"]].add(dev["type"])

    import_block = (
        "from dodal.common.beamlines.beamline_utils import device_factory\n"
        "from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline\n"
        "from dodal.log import set_beamline as set_log_beamline\n"
        "from dodal.utils import BeamlinePrefix, get_beamline_name\n"
    )
    for module, classes in sorted(needed_imports.items()):
        cls_str = ", ".join(sorted(classes))
        import_block += f"from {module} import {cls_str}\n"

    code = f'"""\nGenerated Beamline Configuration\n"""\n\n{import_block}\n'
    code += 'BL = get_beamline_name("i10")\nset_log_beamline(BL)\nset_utils_beamline(BL)\nPREFIX = BeamlinePrefix(BL)\n'

    for section_name, devices in sections.items():
        code += f'\n""" {section_name} """\n'
        for dev in devices:
            f_args = dev.get("factory_args", {})
            f_str = ", ".join([f"{k}={repr(v)}" for k, v in f_args.items()])

            args = ",\n        ".join(
                [f"{k}={format_value(v)}" for k, v in dev["params"].items()]
            )
            body = f"{dev['type']}(\n        {args}\n    )"

            code += (
                f"\n@device_factory({f_str})\n"
                f"def {dev['func']}() -> {dev['type']}:\n"
                f"    return {body}\n"
            )

    return code


def write_beamline_code_to_file(device_dir, output_file):
    code = generate_beamline_code(device_dir)
    with open(output_file, "w") as f:
        f.write(code)
    print(f"Ruffing {output_file}...")
    try:
        subprocess.run(
            ["ruff", "check", "--select", "I", "--fix", output_file], check=True
        )
        subprocess.run(["ruff", "format", output_file], check=True)
        print(f"Done! {output_file} is ready.")
    except subprocess.CalledProcessError as e:
        print(f"Ruff failed: {e}")
    except FileNotFoundError:
        print("Ruff not found in environment. Please install with 'pip install ruff'.")
