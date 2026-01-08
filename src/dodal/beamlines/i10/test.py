from dodal.common.beamlines.config_generator import (
    write_beamline_code_to_file,
)

if __name__ == "__main__":
    write_beamline_code_to_file(
        "/workspaces/dodal/src/dodal/beamlines/i10/",
        "/workspaces/dodal/src/dodal/beamlines/i10/i10.py",
    )
