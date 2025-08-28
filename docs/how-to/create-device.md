Creating a new device
---------------------

Devices in dodal use the ophyd-async framework for hardware abstraction at Diamond Light Source. Before starting, [review where your code should live](../reference/device-standards.rst#where_to_put_devices) to avoid duplication and ensure maintainability.

Reusing an existing class
=========================

Before creating a new device, always check if a suitable class already exists in dodal or ophyd-async. This helps avoid duplication, ensures maintainability, and leverages tested code.

- **Motors:** Use [Motor](https://github.com/bluesky/ophyd-async/blob/main/src/ophyd_async/epics/motor.py) for EPICS motor records.
- **Storage ring signals:** Use [Synchrotron](https://github.com/DiamondLightSource/dodal/blob/main/src/dodal/devices/synchrotron.py).
- **AreaDetectors:** Use [StandardDetector](https://github.com/bluesky/ophyd-async/tree/main/src/ophyd_async/epics/adcore) or [adcore](https://github.com/bluesky/ophyd-async/tree/main/src/ophyd_async/epics/adcore).

Many device classes in `dodal.devices.motors` represent physical relationships between motors, such as `Stage` and `XYStage`.  

For example, only use `XYStage` for two perpendicular motors (e.g. X and Y axes on a sample table):
- Do not use `XYStage` for unrelated motors or for motors that move in the same axis (e.g. coarse and fine adjustment).
- Only a device that represents a group of motors with a physical relationship, should be defined in `motor`.
- If your class define an `XYStage` but you need extra signals or behaviour, extend the `XYStage` class outside the `motor` module.


Device classes that take a list of same device type may use ophyd-async's `DeviceVector`.  
- Avoid dynamic attribute assignment (e.g. dicts of motors) as it hinders type checking and plan writing.  
- Use static attributes and type hints for better IDE support and maintainability.

If a compatible device class exists:
- Use it and add it to the [beamline](./create-beamline.rst) to avoid re-implementation and share improvements.  
- If a device class only differs by PV address, request an alias in the EPICS IOC support module with the relevant controls support team.  
- If that's not possible (e.g. proprietary support), add configurability to the dodal device class, ensuring defaults match existing patterns and that `dodal connect` still works for current devices.

**Only if no suitable class exists**, create a new device that connects to the required signals. During review, refactor to align with existing devices if needed, using inheritance or composition to deduplicate code.  

Writing a device class
======================

To develop a new device, get an initial, working version of your code into the main branch as early as possible. Test it at the beamline, then continuously make and merge small changes into main. This approach prevents pull requests from becoming long-standing issues.

- **Follow the [ophyd-async device implementation guide](https://blueskyproject.io/ophyd-async/main/tutorials/implementing-devices.html)** to structure your device code.
- **Choose the right base class** by consulting the [base class guide](https://blueskyproject.io/ophyd-async/main/how-to/choose-right-baseclass.html), extra consideration should be made if it should be movable see detail in this [movable device guide](../explanations/when-to-extend-movable.md) 
- **Write thorough unit tests** for all expected use cases. Reference the [ophyd-async device test guide](https://blueskyproject.io/ophyd-async/main/tutorials/implementing-devices.html) for best practices.
- **Validate your device on the beamline** and keep notes of any issues for later fixes.
- **Make use of type annotations** so that pyright will validate that you are passing around values that ophyd-async will accept.
- Use `dodal connect <beamline>` to check device connectivity and `cainfo <PV address>` to confirm PVs and datatypes.

**Device best practices for Bluesky plans:**

- Interact with devices in plans only through the Bluesky [messages protocol](https://blueskyproject.io/bluesky/main/msg.html), such as `yield from bps.abs_set(...)` or `yield Msg("set", ...)`.
- Avoid calling device methods directly inside plans (e.g. `device.do_thing()`), as this breaks the abstraction and can lead to unpredictable behaviour.

Example of what **not** to do:
```python
class MyDevice(Device):
    def do_thing(...):
        ...

def my_plan():
    yield from bps.set(...)
    device.do_thing()  # This is bad: do not call device methods directly in plans
```

**Tip:**

- If you are unsure how to represent a PV as a Signal, seek feedback early (for example, by opening a draft PR).
- Whenever possible, merge with existing devices—comprehensive tests help ensure changes do not break current functionality.
- Document any device-specific quirks or limitations for future maintainers.

For further guidance, see the [ophyd-async documentation](https://blueskyproject.io/ophyd-async/main/how-to/choose-interfaces-for-devices.html).
