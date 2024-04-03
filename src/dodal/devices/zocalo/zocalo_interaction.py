import dataclasses
import getpass
import socket
from dataclasses import dataclass

import zocalo.configuration
from workflows.transport import lookup

from dodal.log import LOGGER


def _get_zocalo_connection(environment):
    zc = zocalo.configuration.from_file()
    zc.activate_environment(environment)

    transport = lookup("PikaTransport")()
    transport.connect()
    return transport


@dataclass
class ZocaloStartInfo:
    """
    ispyb_dcid (int): The ID of the data collection in ISPyB
    filename (str): The name of the file that the detector will store into dev/shm
    start_frame_index (int): The index of the first image of this collection within the file
                             written by the detector
    number_of_frames (int): The number of frames in this collection
    message_index (int): Which trigger this is in the detector collection e.g. 0 for the
                         first collection after a single arm, 1 for the next...
    """

    ispyb_dcid: int
    filename: str | None
    start_frame_index: int
    number_of_frames: int
    message_index: int


class ZocaloTrigger:
    """This class just sends 'run_start' and 'run_end' messages to zocalo, it is
    intended to be used in bluesky callback classes. To get results from zocalo back
    into a plan, use the ZocaloResults ophyd device.

    see https://github.com/DiamondLightSource/dodal/wiki/How-to-Interact-with-Zocalo"""

    def __init__(self, environment: str = "artemis"):
        self.zocalo_environment: str = environment

    def _send_to_zocalo(self, parameters: dict):
        transport = _get_zocalo_connection(self.zocalo_environment)

        try:
            message = {
                "recipes": ["mimas"],
                "parameters": parameters,
            }
            header = {
                "zocalo.go.user": getpass.getuser(),
                "zocalo.go.host": socket.gethostname(),
            }
            transport.send("processing_recipe", message, headers=header)
        finally:
            transport.disconnect()

    def run_start(
        self,
        start_data: ZocaloStartInfo,
    ):
        """Tells the data analysis pipeline we have started a run.
        Assumes that appropriate data has already been put into ISPyB

        Args:
            start_data (ZocaloStartInfo): Data about the collection to send to zocalo
        """
        LOGGER.info(f"Starting Zocalo job {start_data}")
        data = dataclasses.asdict(start_data)
        data["event"] = "start"
        self._send_to_zocalo(data)

    def run_end(self, data_collection_id: int):
        """Tells the data analysis pipeline we have finished a run.
        Assumes that appropriate data has already been put into ISPyB

        Args:
            data_collection_id (int): The ID of the data collection representing the
                                    gridscan in ISPyB

        """
        LOGGER.info(f"Ending Zocalo job with ispyb id {data_collection_id}")
        self._send_to_zocalo(
            {
                "event": "end",
                "ispyb_dcid": data_collection_id,
            }
        )
