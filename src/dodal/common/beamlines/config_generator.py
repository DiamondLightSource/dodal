import ast
import os
import subprocess
from collections import defaultdict
from datetime import datetime
from typing import Any

import yaml
from pydantic import BaseModel, Field

from dodal.log import LOGGER


class DecoratorModel(BaseModel):
    name: str = Field(..., description="The decorator name, e.g., 'devices.factory'")
    args: dict[str, Any] = Field(
        default_factory=dict, description="Keyword arguments for the decorator"
    )


class DeviceModel(BaseModel):
    device: str
    type: str
    import_from: str | None = ""
    section: str = "Other"
    params: dict[str, Any] = Field(default_factory=dict)
    # Default to devices.factory() if none provided
    decorators: list[DecoratorModel] = Field(
        default_factory=lambda: [DecoratorModel(name="devices.factory")]
    )


class MasterConfigModel(BaseModel):
    beamline: str
    base_imports: list[str]
    setup_script: str
    device_files: list[str]
    note: str | None = ""


def format_value(v: Any) -> str:
    if isinstance(v, str):
        if "(" in v or ")." in v or v.startswith('f"') or v.startswith("f'"):
            return v
        return f"'{v}'"
    return repr(v)


def beamline_config_generator(config_dir: str) -> str:
    config_file = os.path.join(config_dir, "config.yaml")
    with open(config_file) as f:
        master_raw: dict = yaml.safe_load(f)
        master = MasterConfigModel(**master_raw)

    beamline = master.beamline
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sections = defaultdict(list)
    needed_imports = defaultdict(set)
    seen_functions = set()

    for y_path in master.device_files:
        full_device_path = os.path.join(config_dir, y_path)
        if not os.path.exists(full_device_path):
            LOGGER.warning(f"Device file not found: {full_device_path}")
            continue

        with open(full_device_path) as f:
            content = yaml.safe_load(f)
            device_list_raw = content if isinstance(content, list) else [content]
            for dev_dict in device_list_raw:
                dev = DeviceModel(**dev_dict)
                if dev.device in seen_functions:
                    raise ValueError(f"Duplicate function: {dev.device}")
                seen_functions.add(dev.device)
                sections[dev.section].append(dev)
                needed_imports[dev.import_from].add(dev.type)

    code = f'"""\nGenerated on: {timestamp}\nBeamline: {beamline}\n\nnote:\n{master.note}\n"""\n\n'
    code_lines = master.base_imports[:]
    for module, classes in sorted(needed_imports.items()):
        cls_str = ", ".join(sorted(classes))
        code_lines.append(f"from {module} import {cls_str}")
    code += "\n".join(code_lines) + "\n\n"
    code += master.setup_script.format(beamline=beamline) + "\n"

    for section_name in sorted(sections.keys()):
        code += f'\n\n""" {section_name} """\n'

        for dev in sections[section_name]:
            for dec in dev.decorators:
                arg_str = ", ".join([f"{k}={repr(v)}" for k, v in dec.args.items()])
                code += f"\n@{dec.name}({arg_str})"

            if dev.params:
                args = ",\n        ".join(
                    [f"{k}={format_value(v)}" for k, v in dev.params.items()]
                )
                body = f"{dev.type}(\n        {args}\n    )"
            else:
                body = f"{dev.type}()"

            code += f"\ndef {dev.device}() -> {dev.type}:\n    return {body}\n"
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
    import_map = {}

    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            module = node.module
            for alias in node.names:
                import_map[alias.name] = module

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            base_imports.append(ast.unparse(node))

        elif isinstance(node, ast.FunctionDef):
            ret_type = node.returns.id if isinstance(node.returns, ast.Name) else None

            device_meta = {
                "device": node.name,
                "type": ret_type,
                "import_from": import_map.get(ret_type, "unknown.module"),
            }
            if node.body and isinstance(node.body[0], ast.Return):
                ret_val = node.body[0].value
                if isinstance(ret_val, ast.Call):
                    params = {}
                    for kw in ret_val.keywords:
                        try:
                            params[kw.arg] = ast.literal_eval(kw.value)
                        except (ValueError, TypeError):
                            params[kw.arg] = ast.unparse(kw.value)
                    if params:
                        device_meta["params"] = params

            devices.append(device_meta)

        elif not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)):
            setup_nodes.append(ast.unparse(node))

    beamline_name = os.path.splitext(os.path.basename(py_file_path))[0]
    setup_raw = "\n".join(setup_nodes)
    setup_script = setup_raw.replace(f"'{beamline_name}'", "'{beamline}'")
    device_types = {d["type"] for d in devices}
    filtered_base_imports = []
    for imp in base_imports:
        if not any(f"import {t}" in imp or f", {t}" in imp for t in device_types):
            filtered_base_imports.append(imp)

    os.makedirs(output_dir, exist_ok=True)

    master_config = {
        "beamline": beamline_name,
        "base_imports": filtered_base_imports,
        "setup_script": setup_script,
        "device_files": ["devices.yaml"],
    }

    with open(os.path.join(output_dir, "config.yaml"), "w") as f:
        yaml.dump(master_config, f, sort_keys=False, default_flow_style=False)

    with open(os.path.join(output_dir, "devices.yaml"), "w") as f:
        yaml.dump(devices, f, sort_keys=False, default_flow_style=False)
