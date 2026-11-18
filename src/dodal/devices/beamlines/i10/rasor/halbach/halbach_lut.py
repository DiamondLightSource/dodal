"""Runtime 2D Bilinear Lookup Table for the I10 RASOR 4-magnet Halbach Array."""

from __future__ import annotations

import csv
import io
from pathlib import Path

import numpy as np
from daq_config_server.client import ConfigClient


class HalbachLookupTable:
    """2D bilinear interpolation over
    (H_mT, Field_Angle_Z_deg) -> (m1_unwrapped_deg, m2_unwrapped_deg, m3_unwrapped_deg, m4_unwrapped_deg).

    Restricts setpoints to lie within the calibrated LUT.
    """

    def __init__(
        self,
        h_grid: np.ndarray,
        angle_grid: np.ndarray,
        motor_grid: np.ndarray,
    ) -> None:

        self.h_grid = np.asarray(h_grid, dtype=float)
        self.angle_grid = np.asarray(angle_grid, dtype=float)
        self.motor_grid = np.asarray(motor_grid, dtype=float)

        if self.motor_grid.shape != (len(self.h_grid), len(self.angle_grid), 4):
            raise ValueError(
                f"Expected motor_grid shape {(len(self.h_grid), len(self.angle_grid), 4)}, "
                f"got {self.motor_grid.shape}"
            )

    @classmethod
    def from_csv_contents(
        cls,
        csv_contents: str,
        source: str = "",
    ) -> HalbachLookupTable:
        rows = []
        for row in csv.DictReader(io.StringIO(csv_contents, newline="")):
            rows.append(
                (
                    float(row["H_mT"]),
                    float(row["Field_Angle_Z_deg"]),
                    float(row["m1_unwrapped_deg"]),
                    float(row["m2_unwrapped_deg"]),
                    float(row["m3_unwrapped_deg"]),
                    float(row["m4_unwrapped_deg"]),
                )
            )

        data = np.asarray(rows, dtype=float)
        h_vals = np.unique(data[:, 0])
        ang_vals = np.unique(data[:, 1])
        nh, na = len(h_vals), len(ang_vals)

        if len(data) != nh * na:
            raise ValueError(
                f"CSV at {source} does not form a complete regular 2D grid "
                f"({len(data)} rows vs {nh}x{na}={nh * na})."
            )

        order = np.lexsort((data[:, 1], data[:, 0]))
        sorted_data = data[order]
        motor_grid = sorted_data[:, 2:6].reshape(nh, na, 4)
        return cls(
            h_grid=h_vals,
            angle_grid=ang_vals,
            motor_grid=motor_grid,
        )

    @classmethod
    def from_csv(
        cls,
        csv_path: Path | str,
    ) -> HalbachLookupTable:
        return cls.from_csv_contents(
            Path(csv_path).read_text(encoding="utf-8"),
            source=str(csv_path),
        )

    @classmethod
    def from_config_server(
        cls,
        config_client: ConfigClient,
        lut_path: Path | str,
        reset_cached_result: bool = False,
    ) -> HalbachLookupTable:
        csv_contents = config_client.get_file_contents(
            lut_path,
            reset_cached_result=reset_cached_result,
        )
        return cls.from_csv_contents(csv_contents, source=str(lut_path))

    @property
    def h_limits(self) -> tuple[float, float]:
        return float(self.h_grid[0]), float(self.h_grid[-1])

    @property
    def angle_limits(self) -> tuple[float, float]:
        return float(self.angle_grid[0]), float(self.angle_grid[-1])

    @staticmethod
    def _index_and_weight(grid: np.ndarray, val: float) -> tuple[int, float]:
        """Return cell lower index i in [0, len(grid)-2] and weight w between 0 and 1."""
        idx = int(np.searchsorted(grid, val, side="right")) - 1
        idx = max(0, min(idx, len(grid) - 2))
        g0 = float(grid[idx])
        g1 = float(grid[idx + 1])
        w = (val - g0) / (g1 - g0) if g1 != g0 else 0.0
        return idx, w

    def interpolate(self, h_mt: float, field_angle_z_deg: float) -> np.ndarray:
        """Compute (m1, m2, m3, m4) in degrees via 2D interpolation.

        Args:
            h_mt: Target signed magnetic field strength in mT.
            field_angle_z_deg: Target field angle relative to z-axis in degrees.

        Returns:
            1D numpy array of shape (4,) with [m1, m2, m3, m4] in degrees.

        Raises:
            ValueError: If `h_mt` or `field_angle_z_deg` is outside the calibrated LUT bounds.
        """
        h_min, h_max = self.h_limits
        a_min, a_max = self.angle_limits

        if not (h_min <= h_mt <= h_max):
            raise ValueError(
                f"Target H_mT={h_mt} is outside calibrated LUT bounds [{h_min}, {h_max}] mT."
            )
        if not (a_min <= field_angle_z_deg <= a_max):
            raise ValueError(
                f"Target Field_Angle_Z_deg={field_angle_z_deg} is outside calibrated LUT bounds "
                f"[{a_min}, {a_max}] deg."
            )

        i, th = self._index_and_weight(self.h_grid, float(h_mt))
        j, ta = self._index_and_weight(self.angle_grid, float(field_angle_z_deg))

        m00 = self.motor_grid[i, j]
        m01 = self.motor_grid[i, j + 1]
        m10 = self.motor_grid[i + 1, j]
        m11 = self.motor_grid[i + 1, j + 1]

        return (
            (1.0 - th) * (1.0 - ta) * m00
            + (1.0 - th) * ta * m01
            + th * (1.0 - ta) * m10
            + th * ta * m11
        )
