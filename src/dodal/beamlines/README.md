# Beamlines

Beamline modules are code-as-configuration. They define the set of devices and common device settings needed for a particular beamline or group of similar beamlines (e.g. a beamline and its digital twin). Some of our tooling depends on the convention of _only_ beamline modules going in this package. Common utilities should go somewhere else e.g. `dodal.utils` or `dodal.beamlines.common`.
