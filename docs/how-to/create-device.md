Creating a new device
---------------------

Devices are written using the ophyd-async framework, the hardware abstraction library at Diamond. 

Reusing an existing class
=========================

When creating a new device, first check if there is a device class that claims to support the device: e.g. all EPICS Motor records should use the [Motor](https://github.com/bluesky/ophyd-async/blob/main/src/ophyd_async/epics/motor.py) type; for reading or monitoring signals from the storage ring the [Synchrotron](https://github.com/DiamondLightSource/dodal/blob/main/src/dodal/devices/synchrotron.py) device should be used; AreaDetectors should use the [StandardDetector](https://github.com/bluesky/ophyd-async/blob/main/src/ophyd_async/core/_detector.py) type- of which there are examples in ophyd_async and in dodal.

The module `dodal.devices.motors` defines a series of `Stage`s or groups of motors- a `Stage` represents a physical relationship between motors. For example, an `XYStage` is two perpendicular motors and should not be used for two motors that run parallel to each other (e.g. a coarse motor and a fine adjustment motor in the same axis) or that are unrelated (e.g. attached to different stages with no common frame of reference). Already defined are some relationships with linear and rotational stages. Any device that is a groups of motors only should be additionally defined there, if possible making re-use of the existing classes. Classes that define physical stages but also define additional signals may then extend the `Stage` class outside of the `motors` module for additional behaviour.

Device classes that take a list of devices of a type may make use of the ophyd-async `DeviceVector`, and those that use other collections (e.g. a dict of Motors) to set attributes on themselves at runtime should be avoided- these device classes may appear tempting for their genericness and extensibility, but they will be a hindrance when trying to write plans. When writing plans, the device class is all that is available to the IDE, not the instance that you "just know" has specific fields. Making use of type checking and hints should make writing plans and debugging them a much less frustrating experience, while also enabling discoverability of the devices that are in use.

If there is a compatible device class it should be used- adding it to the [the beamline](./create-beamline.rst)- this prevents reimplementing the device, and allows improvements to be shared. Improving the device to meet your use case is better than starting again.

If a device class is incompatible due to differences in PV address only, first request that an alias is added to the EPICS support module for the IOC - or request support in making that change. Only if it is not possible to add an alias, for example the support module is proprietary, add configurability to the dodal device class, taking care not to break existing devices- e.g. make new fields have a default that matches the existing pattern, and ensure that `dodal connect` is still able to connect to the device for the existing instances.

If the device class is sufficiently different (or you cannot find a similar device), create a device that connects to the required signals and can be tested for your desired behaviour. During the review process, attempts to bring it closer in line with existing devices may allow to deduplicate some parts, through inheritance or composition of the device from existing components.


Writing a device class
======================

The aim should be to get a new device ready for testing it on the beamline as soon as possible, to ensure fast iteration: write a device against your assumptions of how it should work, write tests against those assumptions then test your assumptions on the beamline. Write issues from beamline testing, to resolve offline to reserve as much time for testing that requires the beamline as possible.

Dodal's CLI `dodal connect <beamline>` is a useful way to verify that PV addresses are correct, together with `cainfo <PV address>` to find the datatype of signals.

If you're not sure how to represent a PV as a Signal: ask! Seek feedback early (e.g. by opening a draft PR) and merge with other devices where it makes sense to. The test suite should provide confidence to do so without breaking existing code.


.. _ophyd-async: https://blueskyproject.io/ophyd-async/main/how-to/choose-interfaces-for-devices.html
