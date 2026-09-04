from typing import Any, Final

# By-pass the heavy weight use of config server for simple tests

REALISTIC_SYSTEM_SPECIFICATION: Final[dict[str, Any]] = {
    "lateral_motors": {
        "x": {
            "units": "mm",
            "out": 0.1,
            "threshold": 1.5,
            "max": 75.0,
            "tolerance": 5.0e-3,
        },
        "y": {
            "units": "mm",
            "out": 5.0,
            "threshold": 8.9,
            "max": 98.0,
            "tolerance": 5.0e-3,
        },
    },
    "materials": {
        "aluminium": [
            {
                "valid_energies": {"units": "keV", "lower": 5.0, "upper": 30.0},
                "fit_parameters": {
                    "photon_absorption": 64873.0,
                    "roll_off": -2.96,
                    "residuals_polynomial_coeffs": [],
                },
            }
        ],
        "gold": [
            {
                "valid_energies": {"units": "keV", "lower": 5.0, "upper": 11.5},
                "fit_parameters": {
                    "photon_absorption": 7.87191216e5,
                    "roll_off": -2.52962901,
                    "residuals_polynomial_coeffs": [],
                },
            },
            {
                "valid_energies": {"units": "keV", "lower": 15.0, "upper": 30.0},
                "fit_parameters": {
                    "photon_absorption": 3.63187927e6,
                    "roll_off": -2.59815489,
                    "residuals_polynomial_coeffs": [],
                },
            },
        ],
        "iron": [
            {
                "valid_energies": {"units": "keV", "lower": 8.0, "upper": 30.0},
                "fit_parameters": {
                    "photon_absorption": 1.034347e6,
                    "roll_off": -2.8655,
                    "residuals_polynomial_coeffs": [],
                },
            }
        ],
        "resin1": [
            {
                "valid_energies": {"units": "keV", "lower": 5.0, "upper": 22.0},
                "fit_parameters": {
                    "photon_absorption": 3814.1,
                    "roll_off": -2.81706,
                    "residuals_polynomial_coeffs": [
                        50.9211,
                        -23.6148,
                        4.2138,
                        -0.3814,
                        1.867e-2,
                        -4.709e-4,
                        4.796e-6,
                    ],
                },
            }
        ],
    },
    "wedges": {
        "y": {
            "material": "aluminium",
            "geometry": {"taper_cotangent": 9.3985, "tip": 5.06, "voids": []},
        },
        "x": {
            "material": "resin1",
            "geometry": {
                "taper_cotangent": 7.63359,
                "tip": -3.959,
                "voids": [{"from": 17.66, "to": 18.82}],
            },
        },
    },
    "wheels": {
        "w": {
            "foils": {
                "4": {
                    "absorber": {
                        "material": "iron",
                        "thickness": {"units": "um", "value": 516.07},
                    }
                },
                "2": {
                    "absorber": {
                        "material": "aluminium",
                        "thickness": {"units": "mm", "value": 6.285},
                    }
                },
                "6": {
                    "absorber": {
                        "material": "gold",
                        "thickness": {"units": "micron", "value": 25},
                    }
                },
            },
            "out": 1,
            "permissions": [1],
        }
    },
}


FAKE_SYSTEM_SPECIFICATION_1_JSON: Final[dict[str, Any]] = {
    "lateral_motors": {
        "a": {
            "units": "mm",
            "out": 0.7,
            "threshold": 11.5,
            "max": 61.0,
            "tolerance": 5.0e-3,
        },
        "b": {
            "units": "mm",
            "out": 3.0,
            "threshold": 6.25,
            "max": 85.2,
            "tolerance": 5.0e-3,
        },
    },
    "materials": {
        "argon": [
            {
                "valid_energies": {"units": "keV", "lower": 4.0, "upper": 23.0},
                "fit_parameters": {
                    "photon_absorption": 873.0,
                    "roll_off": -2.6,
                    "residuals_polynomial_coeffs": [],
                },
            }
        ],
        "neon": [
            {
                "valid_energies": {"units": "keV", "lower": 5.0, "upper": 7.5},
                "fit_parameters": {
                    "photon_absorption": 7.87191216e2,
                    "roll_off": -2.51,
                    "residuals_polynomial_coeffs": [],
                },
            },
            {
                "valid_energies": {"units": "keV", "lower": 12.0, "upper": 20.0},
                "fit_parameters": {
                    "photon_absorption": 3.63e2,
                    "roll_off": -2.81,
                    "residuals_polynomial_coeffs": [],
                },
            },
        ],
        "xenon": [
            {
                "valid_energies": {"units": "keV", "lower": 8.0, "upper": 22.4},
                "fit_parameters": {
                    "photon_absorption": 1.43e2,
                    "roll_off": -2.79,
                    "residuals_polynomial_coeffs": [],
                },
            }
        ],
        "krypton": [
            {
                "valid_energies": {"units": "keV", "lower": 5.0, "upper": 12.0},
                "fit_parameters": {
                    "photon_absorption": 384.1,
                    "roll_off": -2.73,
                    "residuals_polynomial_coeffs": [
                        20.901,
                        -13.18,
                        8.38,
                        -5.14,
                        2.7e-2,
                        -4.691e-3,
                        7.746e-5,
                    ],
                },
            }
        ],
    },
    "wedges": {
        "b": {
            "material": "krypton",
            "geometry": {"taper_cotangent": 9.2, "tip": 5.06, "voids": []},
        },
        "a": {
            "material": "argon",
            "geometry": {
                "taper_cotangent": 7.63359,
                "tip": -5.8,
                "voids": [{"from": 15.66, "to": 21.82}],
            },
        },
    },
    "wheels": {
        "w": {
            "foils": {
                "4": {
                    "absorber": {
                        "material": "neon",
                        "thickness": {"units": "um", "value": 516.07},
                    }
                },
                "1": {
                    "absorber": {
                        "material": "neon",
                        "thickness": {"units": "um", "value": 1516.07},
                    }
                },
                "3": {
                    "absorber": {
                        "material": "argon",
                        "thickness": {"units": "mm", "value": 6.285},
                    }
                },
                "6": {
                    "absorber": {
                        "material": "xenon",
                        "thickness": {"units": "micron", "value": 65},
                    }
                },
            },
            "out": 5,
            "permissions": [3, 4, 5],
        }
    },
}
