import os
import subprocess
from collections import defaultdict
from datetime import datetime
from typing import Any

import yaml

from dodal.log import LOGGER


def format_value(v: Any) -> str:
    if isinstance(v, str):
        if "(" in v or ")." in v or v.startswith('f"') or v.startswith("f'"):
            return v
        return f"'{v}'"
    return repr(v)


def get_beamline_code(config_dir: str) -> str:
    config_file = os.path.join(config_dir, "config.yaml")
    with open(config_file) as f:
        master: dict = yaml.safe_load(f)

    beamline = master["beamline"]
    device_files = master.get("device_files", [])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sections = defaultdict(list)
    needed_imports = defaultdict(set)
    seen_functions = set()

    for y_path in device_files:
        full_device_path = os.path.join(config_dir, y_path)
        if not os.path.exists(full_device_path):
            LOGGER.warning(f"Device file not found: {full_device_path}")
            continue

        with open(full_device_path) as f:
            content = yaml.safe_load(f)
            device_list = content if isinstance(content, list) else [content]
            for dev in device_list:
                fname = dev.get("device")
                if fname in seen_functions:
                    raise ValueError(f"Duplicate function: {fname}")
                seen_functions.add(fname)
                sections[dev.get("section", "Other")].append(dev)
                if dev.get("import_from") and dev.get("type"):
                    needed_imports[dev["import_from"]].add(dev["type"])

    code = f'"""\nGenerated on: {timestamp}\nBeamline: {beamline}\n\nnote:\n{master.get("note", "")}\n"""\n\n'

    code_lines = master["base_imports"][:]
    for module, classes in sorted(needed_imports.items()):
        cls_str = ", ".join(sorted(classes))
        code_lines.append(f"from {module} import {cls_str}")
    code += "\n".join(code_lines) + "\n\n"
    code += master["setup_script"].format(beamline=beamline) + "\n"

    for section_name in sorted(sections.keys()):
        code += f'\n\n""" {section_name} """\n'
        for dev in sections[section_name]:
            f_args = dev.get("factory_args", {})
            f_str = ", ".join([f"{k}={repr(v)}" for k, v in f_args.items()])

            if "params" in dev:
                args = ",\n        ".join(
                    [f"{k}={format_value(v)}" for k, v in dev["params"].items()]
                )
                body = f"{dev['type']}(\n        {args}\n    )"
            else:
                body = f"{dev['type']}()"

            code += f"\n@devices.factory({f_str})\ndef {dev['device']}() -> {dev['type']}:\n    return {body}\n"

    try:
        fmt = subprocess.run(
            ["ruff", "format", "-"],
            input=code,
            capture_output=True,
            text=True,
            check=True,
        )
        return fmt.stdout
    except Exception as e:
        LOGGER.error(f"Ruff formatting failed, returning raw code. Error: {e}")
        return code
