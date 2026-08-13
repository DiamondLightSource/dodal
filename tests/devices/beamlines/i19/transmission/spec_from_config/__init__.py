"""Tests of utility library that captures system specification state from JSON.

Beamline scientists have the freedom to edit the JSON files.

The latest state of JSON at system start up should convert to instances of the Spec(ification) classes,
( which are pydantic (v2) BaseModel classes ).
For these validated BaseModels the absorber instrumentation classes are built, that the transmission system logic will govern.
"""
