from bluesky.preprocessors import plan_mutator
from bluesky.utils import Msg, MsgGenerator, make_decorator

from dodal.plans.verify_undulator_gap import CheckUndulatorDevices, verify_undulator_gap


def verify_undulator_gap_before_run_wrapper(
    plan: MsgGenerator,
    devices: CheckUndulatorDevices,
    run_key_to_wrap: str | None = None,
):
    """
    Modifies the wrapped plan so that it checks the undulator gap before the specified run is opened and sets it to the correct value if needed.

    After a beam dump, the undulator gap may not return correctly, scientists have often requested that this check is done before collections.

    Args:
        plan: The plan performing the run.
        devices (CheckUndulatorDevices): Any device composite including the DCM and undulator
        run_key_to_wrap: (str | None): The plan to verify the undulator gap is inserted after the 'open_run' message is seen with
        the matching run key. If not specified, instead wrap the first run encountered.
    """

    # If no run_key specified, make sure we only do check on first run encountered
    _wrapped_run_name: None | str = None

    def head(msg: Msg):
        yield from verify_undulator_gap(devices)
        yield msg

    def insert_plans(msg: Msg):
        nonlocal _wrapped_run_name

        match msg.command:
            case "open_run":
                if (
                    not (run_key_to_wrap or _wrapped_run_name)
                    or run_key_to_wrap is msg.run
                ):
                    _wrapped_run_name = msg.run if msg.run else "unnamed_run"
                    return head(msg), None
        return None, None

    return plan_mutator(plan, insert_plans)


verify_undulator_gap_before_run_decorator = make_decorator(
    verify_undulator_gap_before_run_wrapper
)
