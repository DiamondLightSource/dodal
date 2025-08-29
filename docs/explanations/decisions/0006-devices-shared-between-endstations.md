# 6. Handle devices shared between multiple endstations

Date: 2025-08-27

## Status

Proposed

## Context

Some beamlines have multiple endstations with shared hardware in the optics or experiment hutch, and could potentially be trying to control it at the same time. Any device in the common hutch should only be fully controlled by one endstation at a time - the one that is taking data - but still be readable from the other endstations.

## Decision

The current solution is to have a separate blueapi instance for the shared hutch in order to be able to control the access to all the devices defined there.
For all hardware in the shared optics hutch, the architecture should follow this structure:

- There is a base device in dodal that sends a REST call to the shared blueapi with plan and devices names, as well as the name of the endstation performing the call.
- There are read-only versions of the shared devices in the endstation blueapi which inherit from the base device above and set up the request parameters.
- The real settable devices are only defined in the shared blueapi and should never be called directly from a plan.
- The shared blueapi instance also has an ``AccessControl`` device that reads the endstation in use for beamtime from a PV.
- Every plan should then be wrapped in a decorator that reads the ``AccessControl`` device, check which endstation is making the request and only allows the plan to run if the two values match.


:::{seealso}
[Optics hutch implementation on I19](https://diamondlightsource.github.io/i19-bluesky/main/explanations/decisions/0004-optics-blueapi-architecture.html) for an example.
:::
