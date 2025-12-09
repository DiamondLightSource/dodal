# 5. Encourage aliasing at EPICS level

Date: 2025-05-13

## Status

Proposed

## Context

Many devices have the same functional set of PVs with differing addresses, requiring that either device classes in dodal are generic to support them or duplicate classes are created and must be maintained.

## Decision

Dodal device classes should be made generic before duplicate classes are created, to ensure that upgrades and benefits are shared. Prior to making a device class generic a reasonable attempt should be made to unify the devices at the epics level.

When a new device is onboarded into dodal, there should be clear guidance for the support and controls engineers to use to determine whether an alias should be added to the support module or configurability should be added to the device class.

## Consequences

Documentation on making new devices has been updated and the commitment to trying to standardise devices has been codified.
