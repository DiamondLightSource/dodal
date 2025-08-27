# 6. Handle devices chared between multiple endstations

Date: 2025-08-27

## Status

Proposed

## Context

Some beamlines have multiple endstations with shared hardware in the optics hutch, and could potentially be trying to control it at the same time. Any device in the common hutch should only be fully controlled by one endstation at a time - the one that is taking data - but still be readable from the other endstations.

## Decision

blabla


:::{seealso}
[Optics hutch implementation on I19](https://diamondlightsource.github.io/i19-bluesky/main/explanations/decisions/0004-optics-blueapi-architecture.html) for an example.
:::
