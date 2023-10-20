from pprint import pprint

import bluesky.plans as bp
from bluesky import RunEngine
from ophyd_async.core import DeviceCollector, StaticDirectoryProvider
from ophyd_async.epics.demo import Mover, start_ioc_subprocess
from ophyd_async.panda import PandA
import json

from i22_bluesky.plans.linkam import linkam_plan

from dodal.devices.areadetector.adaravis import SumHDFAravisDetector



if __name__ == "__main__":
    # dp = StaticDirectoryProvider("/exports/mybeamline/data", "sometest")  # for training rig
    dp = StaticDirectoryProvider("/dls/p38/data/2023/cm33874-3", "tmp")  # for p38
    RE = RunEngine()
    pv_prefix = start_ioc_subprocess()

    with DeviceCollector():
        # saxs = SumHDFAravisDetector("BL49P-EA-DET-01:", dp)  # mako
        saxs = SumHDFAravisDetector("BL38P-DI-DCAM-03:", dp)  # was BL49P-EA-DET-01 #manta
        panda = PandA("BL38P-EA-PANDA-01")
        mover = Mover(pv_prefix + "X:")


    RE(
        bp.count([saxs], num=3),
        lambda name, doc: print(json.dumps({"name": name, "doc": doc})),
    )

    RE(
        linkam_plan(
            saxs,
            mover,
            panda,
            start_temp=0.0,
            cool_temp=-5.0,
            cool_step=-1.0,
            cool_rate=1.0,
            heat_temp=3.0,
            heat_step=1.0,
            heat_rate=0.5,
            num_frames=5,
            exposure=0.05,
        ),
        lambda name, doc: print(json.dumps({"name": name, "doc": doc})),
    )

    print("ahg")
