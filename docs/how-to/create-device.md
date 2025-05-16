Creating a new device
---------------------

Devices are written using the ophyd-async framework, the hardware abstraction library at Diamond. 

Reusing an existing class
=========================

When creating a new device, first check if there is a device class that claims to support the device: e.g. all EPICS Motor records should use the [Motor](https://github.com/bluesky/ophyd-async/blob/main/src/ophyd_async/epics/motor.py) type; for reading or monitoring signals from the storage ring the [Synchrotron](https://github.com/DiamondLightSource/dodal/blob/main/src/dodal/devices/synchrotron.py) device should be used; AreaDetectors should use the [StandardDetector](https://github.com/bluesky/ophyd-async/blob/main/src/ophyd_async/core/_detector.py) type- of which there are examples in ophyd_async and in dodal.

If there is a compatible device class it should be used- adding it to the [the beamline](./create-beamline.rst)- this prevents reimplementing the device, and allows improvements to be shared. Improving the device to meet your use case is better than starting again.

If a device class is incompatible due to differences in PV address only, first request that an alias is added to the support module or request support in making that change. Only if it is not possible to add an alias, for example the support module is proprietary, add configurability to the dodal device class, taking care not to break existing devices- e.g. make new fields have a default that matches the existing pattern, and ensure that `dodal connect` is still able to connect to the device for the existing instances.

If the device class is sufficiently different (or you cannot find a similar device), create a device that connects to the required signals and can be tested for your desired behaviour. During the review process, attempts to bring it closer in line with existing devices may allow to deduplicate some parts, through inheritance or composition of the device from existing components.


Writing a device class
======================

The aim should be to get a new device ready for testing it on the beamline as soon as possible, to ensure fast iteration: write a device against your assumptions of how it should work, write tests against those assumptions then test your assumptions on the beamline. Write issues from beamline testing, to resolve offline to reserve as much time for testing that requires the beamline as possible.

Dodal's CLI `dodal connect <beamline>` is a useful way to verify that PV addresses are correct, together with `cainfo <PV address>` to find the datatype of signals.

If you're not sure how to represent a PV as a Signal: ask! Seek feedback early (e.g. by opening a draft PR) and merge with other devices where it makes sense to. The test suite should provide confidence to do so without breaking existing code.


.. _ophyd-async: https://blueskyproject.io/ophyd-async/main/how-to/choose-interfaces-for-devices.html
