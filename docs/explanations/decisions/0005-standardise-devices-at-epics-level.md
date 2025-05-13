# 5. Encourage aliasing at EPICS level

Date: 2025-05-13

## Status

Proposed

## Context

Many devices have the same set of PVs with differing addresses, requiring that either device classes in dodal are generic to support them, to prevent duplicate classes being created and maintained.

## Decision

When a new device is onboarded into dodal, there should be clear guidance for the support and controls engineers to use to determine whether an alias should be added to the support module or configurability should be added to the device class.

## Consequences

The following process should be followed when adding a device:

1. Check if there is a device class that claims to support the device: e.g. all EPICS Motor records should use the [Motor](https://github.com/bluesky/ophyd-async/blob/main/src/ophyd_async/epics/motor.py) type; for reading or monitoring signals from the storage ring the [Synchrotron](https://github.com/DiamondLightSource/dodal/blob/main/src/dodal/devices/synchrotron.py) device should be used.
    - If there is, and it is compatible, it should be used. This prevents reimplementing the device, and allows improvements to be shared.
    - If there is, and if is not compatible due to differences in PV address only, request that an alias is added to the support module by the controls engineer, or request they support and review you making the change - this will help distribute knowledge in addition to the other benefits.
    - If it is not possible to add an alias, for example the support module is proprietary, add configurability to the dodal device class, taking care not to break existing devices- e.g. make any defaults use the existing pattern, not your new pattern
2. If the device class is sufficiently different (or you cannot find a similar device) in the first instance create a device that connects to the required signals and can be tested for your desired behaviour. During the review process, attempts to bring it closer in line with existing devices may allow to deduplicate some parts, through inheritance or composition of the device from existing components.
