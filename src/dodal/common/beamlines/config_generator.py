import ast
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


def translate_beamline_py_config_to_yaml(py_file_path: str, output_dir: str):
    with open(py_file_path) as f:
        source = f.read()
        tree = ast.parse(source)

    devices = []
    base_imports = []
    setup_nodes = []

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            base_imports.append(ast.unparse(node))

        elif isinstance(node, ast.FunctionDef):
            device_meta = {
                "device": node.name,
                "type": node.returns.id if isinstance(node.returns, ast.Name) else None,
            }

            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and "factory" in ast.unparse(
                    decorator
                ):
                    f_args = {
                        kw.arg: ast.literal_eval(kw.value) for kw in decorator.keywords
                    }
                    if f_args:
                        device_meta["factory_args"] = f_args

            ret_stmt = node.body[0]
            if isinstance(ret_stmt, ast.Return) and isinstance(
                ret_stmt.value, ast.Call
            ):
                params = {}
                for kw in ret_stmt.value.keywords:
                    try:
                        params[kw.arg] = ast.literal_eval(kw.value)
                    except ValueError:
                        params[kw.arg] = ast.unparse(kw.value)
                if params:
                    device_meta["params"] = params

            devices.append(device_meta)

        elif not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Constant):
            setup_nodes.append(ast.unparse(node))

    beamline_name = os.path.splitext(os.path.basename(py_file_path))[0]
    setup_script = "\n".join(setup_nodes).replace(f"'{beamline_name}'", "'{beamline}'")

    os.makedirs(output_dir, exist_ok=True)

    master_config = {
        "beamline": beamline_name,
        "output_file": os.path.basename(py_file_path),
        "base_imports": base_imports,
        "setup_script": setup_script,
        "device_files": ["devices.yaml"],
    }

    with open(os.path.join(output_dir, "config.yaml"), "w") as f:
        yaml.dump(master_config, f, sort_keys=False, default_flow_style=False)

    with open(os.path.join(output_dir, "devices.yaml"), "w") as f:
        yaml.dump(devices, f, sort_keys=False, default_flow_style=False)

    print(f"Successfully back-translated {py_file_path} to {output_dir}")
