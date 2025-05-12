"""A small temporary device to set and read the filename template from the pilatus"""

import re

from ophyd_async.core import StandardReadable, derived_signal_r
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class PilatusMetadata(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.filename = epics_signal_rw(str, prefix + "cam1:FileName")
        self.template = epics_signal_r(str, prefix + "cam1:FileTemplate_RBV")
        self.filenumber = epics_signal_r(int, prefix + "cam1:FileNumber_RBV")
        with self.add_children_as_readables():
            self.filename_template = derived_signal_r(
                self._get_full_filename_template,
                filename=self.filename,
                filename_template=self.template,
                file_number=self.filenumber,
            )
        super().__init__(name)

    def _get_full_filename_template(
        self, filename: str, filename_template: str, file_number: int
    ) -> str:
        """
        Get the template file path by querying the detector PVs.
        Mirror the construction that the PPU does.

        Returns: A template string, with the image numbers replaced with '#'
        """
        # Exploit fact that passing negative numbers will put the - before the 0's
        expected_filename = str(
            filename_template % (filename, f"{file_number:05d}_", -9)
        )
        # Now, find the -09 part of this
        numberpart = re.search(r"(-0+9)", expected_filename)
        assert numberpart is not None
        template_fill = "#" * len(numberpart.group(0))
        return (
            expected_filename[: numberpart.start()]
            + template_fill
            + expected_filename[numberpart.end() :]
        )
