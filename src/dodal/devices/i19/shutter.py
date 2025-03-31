from enum import Enum

from aiohttp import ClientSession
from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable, StandardReadableFormat
from ophyd_async.epics.core import epics_signal_r

from dodal.devices.hutch_shutter import ShutterDemand, ShutterState
from dodal.log import LOGGER

OPTICS_BLUEAPI_URL = "https://i19-blueapi.diamond.ac.uk"


class HutchState(str, Enum):
    EH1 = "EH1"
    EH2 = "EH2"


class AccessControlledShutter(StandardReadable, Movable[ShutterDemand]):
    """ I19-specific device to operate the hutch shutter.

    This device will send a REST call to the blueapi instance controlling the optics \
    hutch running on the I19 cluster, which will evaluate the current hutch in use vs \
    the hutch sending the request and decide if the plan will be run or not.
    As the two hutches are located in series, checking the hutch in use is necessary to \
    avoid accidentally operating the shutter from one hutch while the other has beamtime.

    The name of the hutch that wants to operate the shutter should be passed to the \
    device upon instantiation.

    For details see the architecture described in \
    https://github.com/DiamondLightSource/i19-bluesky/issues/30.
    """

    def __init__(self, prefix: str, hutch: HutchState, name: str = "") -> None:
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.shutter_status = epics_signal_r(ShutterState, f"{prefix}STA")
        self.hutch_request = hutch
        self.url = OPTICS_BLUEAPI_URL
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: ShutterDemand):
        REQUEST_PARAMS = {
            "name": "operate_shutter_plan",
            "params": {
                "experiment_hutch": self.hutch_request.value,
                "access_device": "access_control",  # Device name in i19-blueapi
                "shutter_demand": value,
            },
        }
        async with ClientSession(base_url=self.url, raise_for_status=True) as session:
            # First submit the plan to the worker
            async with session.post("/tasks", data=REQUEST_PARAMS) as response:
                LOGGER.debug(
                    f"Task submitted to the worker, response status: {response.status}"
                )

                try:
                    data = await response.json()
                    task_id = data["task_id"]
                except Exception as e:
                    LOGGER.error(
                        f"Failed to get task_id from {self.url}/tasks POST. ({e})"
                    )
                    raise
            # Then set the task as active and run asap
            async with session.put(
                "/worker/tasks", data={"task_id": task_id}
            ) as response:
                if not response.ok:
                    LOGGER.warning(
                        f"""Unable to operate the shutter.
                        Session PUT responded with {response.status}: {response.reason}.
                        """
                    )
                    return
                LOGGER.debug(f"Run operate shutter plan, task_id: {task_id}")
