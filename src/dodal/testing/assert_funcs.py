import inspect
import re
from collections.abc import Callable
from typing import Any

from dodal.utils import make_all_devices

_INJECT_RE = re.compile(r"inject\(['\"]([^'\"]+)['\"]\)")


def find_inject_args(
    func: Callable[..., Any], *, allow_any_str_default: bool = True
) -> list[str]:
    """
    Return a list of injection names found as defaults on `func`'s parameters.

    - If default is a marker object with .name / .inject_name / __inject_name__, use that.
    - If default is a str and the parameter annotation is not `str`, treat that string
      as an injection name (controlled by allow_any_str_default).
    - Fallback: try to parse repr(default) for inject('name').
    """
    sig = inspect.signature(func)
    found: list[str] = []

    for param in sig.parameters.values():
        default = param.default
        if default is inspect._empty:
            continue

        ann = param.annotation
        ann_is_str = ann is str or getattr(ann, "__origin__", None) is str

        # 1) duck-typed marker objects
        for attr in ("name", "inject_name", "__inject_name__"):
            if hasattr(default, attr):
                val = getattr(default, attr)
                if isinstance(val, str):
                    found.append(val)
                    break
        else:
            # 2) plain string default -> treat as injection if annotation != str
            if isinstance(default, str) and not ann_is_str and allow_any_str_default:
                found.append(default)
                continue

            # 3) fallback: parse repr for inject('name')
            m = _INJECT_RE.search(repr(default))
            if m:
                found.append(m.group(1))

    return found


def assert_plan_has_valid_inject_devices_for_beamline(beamline: str, plan) -> None:
    beamline_devices, _ = make_all_devices("dodal.beamlines." + beamline, mock=True)
    beamline_device_names = list(beamline_devices.keys())
    plan_inject_device_names = find_inject_args(plan)
    try:
        assert set(plan_inject_device_names).issubset(beamline_device_names)
    except AssertionError as e:
        raise AssertionError(
            f"plan had default devices {plan_inject_device_names} but beamline only",
            "had these device configured {beamline_device_names}.",
        ) from e
