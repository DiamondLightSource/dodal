from dodal.common.beamlines.config_generator import generate_beamline

CONFIG_DIR = "/workspaces/dodal/src/dodal/devices/i10/i10_config/"

try:
    code = generate_beamline(CONFIG_DIR)
    exec(code, globals())

except Exception as e:
    import logging

    logging.getLogger("dodal").error(f"Failed to generate beamline from YAML: {e}")
    raise
