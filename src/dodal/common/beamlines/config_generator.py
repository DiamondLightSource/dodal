import os
import subprocess
from collections import defaultdict
from datetime import datetime
from typing import Any

import yaml

from dodal.log import LOGGER


def format_value(v: Any) -> str:
    """
    Handles literals, f-strings, and backtick f-strings.
    """
    if isinstance(v, str):
        # Code pass-through (function calls, attribute access, standard f-strings)
        if "(" in v or ")." in v or v.startswith('f"') or v.startswith("f'"):
            return v
        return f"'{v}'"
    return repr(v)


def generate_beamline(config_dir: str) -> None:
    # Generate beamline configuration code based on YAML files
    config_file = os.path.join(config_dir, "config.yaml")
    with open(config_file) as f:
        master: dict = yaml.safe_load(f)

    beamline = master["beamline"]
    output_file = master["output_file"]
    device_files = master.get("device_files", [])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sections = defaultdict(list)
    needed_imports = defaultdict(set)
    seen_functions = set()

    # Generate devices from YAML files
    for y_path in device_files:
        full_device_path = os.path.join(config_dir, y_path)
        if not os.path.exists(full_device_path):
            LOGGER.warning(msg=f"Defined device file not found: {full_device_path}")
            continue

        with open(full_device_path) as f:
            content: dict = yaml.safe_load(f)
            device_list: list[dict] = (
                content if isinstance(content, list) else [content]
            )

            for dev in device_list:
                fname = dev.get("func")
                if fname in seen_functions:
                    raise ValueError(
                        f"Duplicate function name detected: '{fname}' in {y_path}"
                    )
                seen_functions.add(fname)

                sections[dev.get("section", "Other")].append(dev)
                if dev.get("import_from") and dev.get("type"):
                    needed_imports[dev["import_from"]].add(dev["type"])

    # Build Note and Import Block
    code = (
        '"""\n'
        f"Generated on: {timestamp}\n"
        f"Beamline: {beamline}\n\n"
        "note:\n"
        f"{master.get('note', '')}\n"
        '"""\n\n'
    )

    code_lines: list = master["base_imports"][:]
    for module, classes in sorted(needed_imports.items()):
        cls_str = ", ".join(sorted(classes))
        code_lines.append(f"from {module} import {cls_str}")

    code += "\n".join(code_lines) + "\n\n"

    # Build Setup Script
    code += master["setup_script"].format(beamline=beamline) + "\n"

    # Build Devices
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

            code += (
                f"\n@devices.factory({f_str})"
                f"\ndef {dev['func']}() -> {dev['type']}:"
                f"\n    return {body}\n"
            )

    # Write and Ruff
    with open(output_file, "w") as f:
        f.write(code)

    try:
        subprocess.run(
            ["ruff", "check", "--select", "I", "--fix", output_file], check=True
        )
        subprocess.run(["ruff", "format", output_file], check=True)
        print(f"Generated {output_file} successfully.")
    except Exception as e:
        print(f"File saved to {output_file}, but Ruff failed: {e}")
