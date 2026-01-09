import os

from dodal.common.beamlines.config_generator import generate_beamline

current_dir = os.path.dirname(__file__)
beamline_name = os.path.splitext(os.path.basename(__file__))[0]
CONFIG_DIR = os.path.join(current_dir, "configs", beamline_name)

try:
    code = generate_beamline(CONFIG_DIR)
    exec(code, globals())

except Exception as e:
    import logging

    logging.getLogger("dodal").error(f"Failed to generate beamline from YAML: {e}")
    raise
