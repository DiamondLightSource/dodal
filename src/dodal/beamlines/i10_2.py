import os

from dodal.common.beamlines.config_generator import beamline_config_generator

current_dir = os.path.dirname(__file__)
beamline_name = os.path.splitext(os.path.basename(__file__))[0]
CONFIG_DIR = os.path.join(current_dir, "configs", beamline_name)

# Generate and inject
code = beamline_config_generator(CONFIG_DIR)
exec(code, globals())
