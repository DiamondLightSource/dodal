import threading
from functools import partial
from time import sleep

import bluesky.plan_stubs as bps
from bluesky import RunEngine
from ophyd import Component, Device, Signal
from ophyd.status import Status


class MyDevice(Device):
    class ArmingSignal(Signal):
        def set(self, value, *, timeout=None, settle_time=None, **kwargs):
            return self.parent.do_full_arm_func()

    do_arm: ArmingSignal = Component(ArmingSignal)

    def do_full_arm_func(self):
        statuses = [Status(1), Status(2), Status(3)]

        print(statuses)

        self.do_arm_func_1(statuses[0])
        statuses[0].add_callback(partial(self.do_arm_func_2, new_status=statuses[1]))
        statuses[1].add_callback(partial(self.do_arm_func_3, new_status=statuses[2]))

        return statuses[0] & statuses[1] & statuses[2]

    def do_arm_func_1(self, status):
        def wait_then_set_status():
            print("doing arming function")
            sleep(1)
            status.set_finished()

        threading.Thread(target=wait_then_set_status, daemon=True).start()

    def do_arm_func_2(self, old_status, new_status):
        def wait_then_set_status():
            print("doing arming function 2 ")
            sleep(3)
            new_status.set_finished()

        threading.Thread(target=wait_then_set_status, daemon=True).start()

    def do_arm_func_3(self, old_status, new_status):
        def wait_then_set_status():
            print("doing arming function 3")
            sleep(0.5)
            new_status.set_finished()

        threading.Thread(target=wait_then_set_status, daemon=True).start()


def my_plan():
    dev = MyDevice(name="test")

    yield from bps.abs_set(dev.do_arm, 1, group="arming")
    print("Done move, waiting")

    # yield from bps.stage(dev)

    # status = []
    # status[0] = dev.do_arm_func()

    # def set_status(status, func1, func2, end):
    #     status[0] = func1()

    # status[0].finished_cb = set_status(
    #     status,
    #     dev.do_arm_func_2,
    #     dev.do_arm_func_3,
    # )

    yield from bps.wait("arming")
    print("Finished waiting")


# make a run engine, run plan
RE = RunEngine({})
dev = MyDevice(name="test")
RE(my_plan())
