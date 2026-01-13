import os

from dodal.common.beamlines.config_generator import get_beamline_code

current_dir = os.path.dirname(__file__)
beamline_name = os.path.splitext(os.path.basename(__file__))[0]
CONFIG_DIR = os.path.join(current_dir, "configs", beamline_name)

# Generate and inject
code = get_beamline_code(CONFIG_DIR)
exec(code, globals())
