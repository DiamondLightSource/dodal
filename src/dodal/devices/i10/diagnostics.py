from ophyd_async.core import (
    Device,
    StandardReadable,
    StrictEnum,
)
from ophyd_async.core import StandardReadableFormat as Format
from ophyd_async.core._device import DeviceConnector
from ophyd_async.epics.adaravis import AravisDriverIO
from ophyd_async.epics.adcore import SingleTriggerDetector
from ophyd_async.epics.core import (
    epics_signal_r,
    epics_signal_rw,
)

from dodal.devices.current_amplifiers import (
    CurrentAmpDet,
    Femto3xxGainTable,
    Femto3xxGainToCurrentTable,
    Femto3xxRaiseTime,
    FemtoDDPCA,
    StruckScaler,
)
from dodal.devices.positioner import create_positioner


class D3Position(StrictEnum):
    NOTHING = "Nothing"
    GRID = "Grid"


class D5Position(StrictEnum):
    CELL_IN = "Cell In"
    CELL_OUT = "Cell Out"


class D5APosition(StrictEnum):
    OUT_OF_THE_BEAM = "Out of the beam"
    DIODE = "Diode"
    BLADE = "Blade"
    LA = "La ref"
    GD = "Gd ref"
    YB = "Yb ref"
    GRID = "Grid"


class D6Position(StrictEnum):
    DIODE_OUT = "Diode Out"
    DIODE_IN = "Diode In"
    AU_MESH = "Au Mesh"


class D7Position(StrictEnum):
    OUT = "Out"
    SHUTTER = "Shutter"


class InOutTable(StrictEnum):
    MOVE_IN = "Move In"
    MOVE_OUT = "Move Out"
    RESET = "Reset"


class InOutReadBackTable(StrictEnum):
    MOVE_IN = "Moving In"
    MOVE_OUT = "Moving Out"
    IN_BEAM = "In Beam"
    FAULT = "Fault"
    OUT_OF_BEAM = "Out of Beam"


class I10PneumaticStage(StandardReadable):
    """Pneumatic stage only has two real positions in or out.
    Use for fluorescent screen which can be insert into the x-ray beam.
    Most often use in conjunction with a webcam to locate the x-ray beam."""

    def __init__(
        self,
        prefix: str,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables(Format.HINTED_SIGNAL):
            self.stage_position_set = epics_signal_rw(
                InOutTable,
                read_pv=prefix + "CON",
            )
            self.stage_position_readback = epics_signal_r(
                InOutReadBackTable,
                read_pv=prefix + "STA",
            )
        super().__init__(name=name)


class ScreenCam(Device):
    """Compound device of pneumatic stage(fluorescent screen) and webcam"""

    def __init__(
        self,
        prefix: str,
        cam_infix="DCAM:",
        name: str = "",
    ) -> None:
        self.screen_stage = I10PneumaticStage(
            prefix=prefix,
        )
        cam_pv = prefix + cam_infix
        self.centroid_x = epics_signal_r(float, read_pv=f"{cam_pv}STAT:CentroidX_RBV")
        self.centroid_y = epics_signal_r(float, read_pv=f"{cam_pv}STAT:CentroidY_RBV")
        self.single_trigger_centroid = SingleTriggerDetector(
            drv=AravisDriverIO(prefix=cam_pv + "CAM:"),
            read_uncached=[
                self.centroid_x,
                self.centroid_y,
            ],
        )
        super().__init__(name=name)


class FullDiagnostic(Device):
    """Compound device of a diagnostic with screen, webcam and Positioner stage."""

    def __init__(
        self,
        prefix: str,
        positioner_enum: type[StrictEnum],
        positioner_suffix: str,
        cam_infix: str = "DCAM:",
        name: str = "",
    ) -> None:
        self.positioner = create_positioner(
            positioner_enum,
            prefix + positioner_suffix,
        )
        self.screen = ScreenCam(
            prefix,
            cam_infix,
            name,
        )
        super().__init__(name)


class I10Diagnostic(Device):
    """Collection of all the diagnostic stage on i10."""

    def __init__(self, prefix, name: str = "") -> None:
        self.d1 = ScreenCam(prefix=prefix + "PHDGN-01:")
        self.d2 = ScreenCam(prefix=prefix + "PHDGN-02:")
        self.d3 = FullDiagnostic(
            prefix=prefix + "PHDGN-03:",
            positioner_enum=D3Position,
            positioner_suffix="DET:X",
        )
        self.d4 = ScreenCam(prefix=prefix + "PHDGN-04:")
        self.d5 = create_positioner(D5Position, f"{prefix}IONC-01:Y")
        self.d5A = create_positioner(D5APosition, f"{prefix}PHDGN-06:DET:X")
        self.d6 = FullDiagnostic(f"{prefix}PHDGN-05:", D6Position, "DET:X")
        self.d7 = create_positioner(D7Position, f"{prefix}PHDGN-07:Y")

        super().__init__(name)


class I10Diagnostic5ADet(Device):
    """Diagnostic 5a detection with drain current and photo diode"""

    def __init__(
        self, prefix: str, name: str = "", connector: DeviceConnector | None = None
    ) -> None:
        self.drain_current = CurrentAmpDet(
            current_amp=FemtoDDPCA(
                prefix=prefix + "IAMP-06:",
                suffix="GAIN",
                gain_table=Femto3xxGainTable,
                gain_to_current_table=Femto3xxGainToCurrentTable,
                raise_timetable=Femto3xxRaiseTime,
            ),
            counter=StruckScaler(prefix=prefix + "SCLR-02:SCALER2", suffix=".S17"),
        )
        self.diode = CurrentAmpDet(
            FemtoDDPCA(
                prefix=prefix + "IAMP-05:",
                suffix="GAIN",
                gain_table=Femto3xxGainTable,
                gain_to_current_table=Femto3xxGainToCurrentTable,
                raise_timetable=Femto3xxRaiseTime,
            ),
            counter=StruckScaler(prefix=prefix + "SCLR-02:SCALER2", suffix=".S18"),
        )
        super().__init__(name, connector)
