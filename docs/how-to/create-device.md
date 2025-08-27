Creating a new device
---------------------

Devices in dodal use the ophyd-async framework for hardware abstraction at Diamond Light Source. Before starting, [review where your code should live](../reference/device-standards.rst#where_to_put_devices) to avoid duplication and ensure maintainability.

Reusing an existing class
=========================

When creating a new device, always check if a device class already supports your hardware:
- **Motors:** Use [Motor](https://github.com/bluesky/ophyd-async/blob/main/src/ophyd_async/epics/motor.py) for EPICS motor records.
- **Storage ring signals:** Use [Synchrotron](https://github.com/DiamondLightSource/dodal/blob/main/src/dodal/devices/synchrotron.py).
- **AreaDetectors:** Use [StandardDetector](https://github.com/bluesky/ophyd-async/tree/main/src/ophyd_async/epics/adcore) or [adcore](https://github.com/bluesky/ophyd-async/tree/main/src/ophyd_async/epics/adcore).

The module `dodal.devices.motors` defines physical relationships between motors, such as `Stage` and `XYStage`.  
For example, an `XYStage` is for two perpendicular motors (e.g. X and Y axes on a sample table):

.. literalinclude:: ../../src/dodal/devices/motors.py
    :start-at: class XYStage(Stage):
    :end-at: super().__init__(name=name)

Do not use `XYStage` for unrelated motors or for motors that move in the same axis (e.g. coarse and fine adjustment).  
If your device is a group of motors with a physical relationship, define it in `motors` if possible.  
If you need extra signals or behaviour, extend the `Stage` class outside the `motors` module.

Device classes that take a list of devices may use ophyd-async's `DeviceVector`.  
Avoid dynamic attribute assignment (e.g. dicts of motors) as it hinders type checking and plan writing.  
Use static attributes and type hints for better IDE support and maintainability.


If a compatible device class exists, use it—add it to the [beamline](./create-beamline.rst) to avoid re-implementation and share improvements.  
If a device class only differs by PV address, request an alias in the EPICS IOC support module.  
If that's not possible (e.g. proprietary support), add configurability to the dodal device class, ensuring defaults match existing patterns and that `dodal connect` still works for current devices.

If no suitable class exists, create a new device that connects to the required signals and is testable.  
During review, refactor to align with existing devices if needed, using inheritance or composition to deduplicate code.


Writing a device class
======================

Aim to get your device ready for beamline testing quickly:
- Follow the [ophyd-async device implementation guide](https://blueskyproject.io/ophyd-async/main/tutorials/implementing-devices.html) to structure your device.
- Write thorough tests for all use cases, referencing the [ophyd-async device test guide](https://blueskyproject.io/ophyd-async/main/tutorials/implementing-devices.html).
- Validate your device on the beamline and keep notes of any issues for later fixes.
- Use `dodal connect <beamline>` to check device connectivity and `cainfo <PV address>` to confirm PVs and datatypes.

**Important:**  
Device interaction in plans should only happen through Bluesky [messages protocol](https://blueskyproject.io/bluesky/main/msg.html) (e.g. `yield from bps.abs_set(...)` or `yield Msg("set", ...)` ).  
Direct method calls on device objects inside plans (such as `device.do_thing()`) should be avoided, as this breaks the abstraction and can lead to unpredictable behaviour.

Example of what **not** to do:
```python
class MyDevice(Device):
    def do_thing(...):
        ...

def my_plan():
    yield from bps.set(...)
    device.do_thing()  # This is bad: do not call device methods directly in plans
```


If you are unsure how to represent a PV as a Signal, seek feedback early (for example, by opening a draft PR).  
Whenever possible, merge with existing devices—comprehensive tests help ensure changes do not break current functionality.


For further guidance, see the [ophyd-async documentation](https://blueskyproject.io/ophyd-async/main/how-to/choose-interfaces-for-devices.html).
