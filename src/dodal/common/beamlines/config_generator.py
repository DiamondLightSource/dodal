import yaml


def generate_python_from_yaml(yaml_path):
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    code = f'"""\nnote:\n{data["note"]}"""\n\n'

    code += (
        "from dodal.common.beamlines.beamline_utils import device_factory\n"
        "from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline\n"
        "from dodal.devices.current_amplifiers import CurrentAmpDet\n"
        "from dodal.devices.i10 import (\n"
        "    I10Diagnostic,\n"
        "    I10Diagnostic5ADet,\n"
        "    I10Slits,\n"
        "    I10SlitsDrainCurrent,\n"
        "    PiezoMirror,\n"
        ")\n"
        "from dodal.devices.i10.diagnostics import I10Diagnostic, I10Diagnostic5ADet\n"
        "from dodal.devices.i10.rasor.rasor_current_amp import RasorFemto, RasorSR570\n"
        "from dodal.devices.i10.rasor.rasor_motors import (\n"
        "    DetSlits,\n"
        "    Diffractometer,\n"
        "    PaStage,\n"
        ")\n"
        "from dodal.devices.i10.rasor.rasor_scaler_cards import RasorScalerCard1\n"
        "from dodal.devices.motors import XYStage, XYZStage\n"
        "from dodal.devices.temperture_controller import (\n"
        "    Lakeshore340,\n"
        ")\n"
        "from dodal.log import set_beamline as set_log_beamline\n"
        "from dodal.utils import BeamlinePrefix, get_beamline_name\n\n"
    )

    bl = data["beamline"]
    code += f'BL = get_beamline_name("{bl}")\n'
    code += (
        "set_log_beamline(BL)\nset_utils_beamline(BL)\nPREFIX = BeamlinePrefix(BL)\n"
    )

    for section in data["sections"]:
        code += f'\n"""{section["title"]}"""\n'

        for dev in section["devices"]:
            f_args = dev.get("factory_args", {})
            factory_params = []
            for k, v in f_args.items():
                val = str(v) if not isinstance(v, str) else f"'{v}'"
                factory_params.append(f"{k}={val}")

            factory_line = f"@device_factory({', '.join(factory_params)})"
            if "params" in dev:
                args = ",\n        ".join(
                    [f"{k}={v}" for k, v in dev["params"].items()]
                )
                body = f"{dev['type']}(\n        {args},\n    )"
            else:
                body = f'{dev["type"]}(prefix=f"{dev["prefix"]}")'

            code += (
                f"\n{factory_line}\n"
                f"def {dev['func']}() -> {dev['type']}:\n"
                f"    return {body}\n"
            )

    return code
