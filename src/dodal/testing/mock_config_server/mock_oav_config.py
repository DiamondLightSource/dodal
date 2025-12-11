from daq_config_server.converters.models import (
    DisplayConfig,
    DisplayConfigData,
)


class MockOavConfig:
    @staticmethod
    def get_oav_config_json():
        return {
            "exposure": 0.075,
            "acqPeriod": 0.05,
            "gain": 1.0,
            "minheight": 70,
            "oav": "OAV",
            "mxsc_input": "CAM",
            "min_callback_time": 0.080,
            "close_ksize": 11,
            "direction": 0,
            "pinTipCentring": {
                "zoom": 1.0,
                "preprocess": 8,
                "preProcessKSize": 21,
                "CannyEdgeUpperThreshold": 20.0,
                "CannyEdgeLowerThreshold": 5.0,
                "brightness": 20,
                "max_tip_distance": 300,
                "mxsc_input": "proc",
                "minheight": 10,
                "min_callback_time": 0.15,
                "filename": "/dls_sw/prod/R3.14.12.7/support/adPython/2-1-11/adPythonApp/scripts/adPythonMxSampleDetect.py",
            },
            "loopCentring": {
                "zoom": 5.0,
                "preprocess": 8,
                "preProcessKSize": 21,
                "CannyEdgeUpperThreshold": 20.0,
                "CannyEdgeLowerThreshold": 5.0,
                "brightness": 20,
                "filename": "/dls_sw/prod/R3.14.12.7/support/adPython/2-1-11/adPythonApp/scripts/adPythonMxSampleDetect.py",
                "max_tip_distance": 300,
                "minheight": 10,
            },
            "xrayCentring": {
                "zoom": 7.5,
                "preprocess": 8,
                "preProcessKSize": 31,
                "CannyEdgeUpperThreshold": 30.0,
                "CannyEdgeLowerThreshold": 5.0,
                "close_ksize": 3,
                "filename": "/dls_sw/prod/R3.14.12.7/support/adPython/2-1-11/adPythonApp/scripts/adPythonMxSampleDetect.py",
                "brightness": 80,
            },
            "rotationAxisAlign": {
                "zoom": 10.0,
                "preprocess": 8,
                "preProcessKSize": 21,
                "CannyEdgeUpperThreshold": 20.0,
                "CannyEdgeLowerThreshold": 5.0,
                "filename": "/dls_sw/prod/R3.14.12.7/support/adPython/2-1-11/adPythonApp/scripts/adPythonMxSampleDetect.py",
                "brightness": 100,
            },
            "SmargonOffsets1": {
                "zoom": 1.0,
                "preprocess": 8,
                "preProcessKSize": 21,
                "CannyEdgeUpperThreshold": 50.0,
                "CannyEdgeLowerThreshold": 5.0,
                "brightness": 80,
            },
            "SmargonOffsets2": {
                "zoom": 5.0,
                "preprocess": 8,
                "preProcessKSize": 11,
                "CannyEdgeUpperThreshold": 50.0,
                "CannyEdgeLowerThreshold": 5.0,
                "brightness": 90,
            },
        }

    @staticmethod
    def get_zoom_params_file():
        return {
            "JCameraManSettings": {
                "levels": {
                    "zoomLevel": [
                        {
                            "level": "1.0",
                            "position": "0",
                            "micronsPerXPixel": "2.87",
                            "micronsPerYPixel": "2.87",
                        },
                        {
                            "level": "2.5",
                            "position": "10",
                            "micronsPerXPixel": "2.31",
                            "micronsPerYPixel": "2.31",
                        },
                        {
                            "level": "5.0",
                            "position": "25",
                            "micronsPerXPixel": "1.58",
                            "micronsPerYPixel": "1.58",
                        },
                        {
                            "level": "7.5",
                            "position": "50",
                            "micronsPerXPixel": "0.806",
                            "micronsPerYPixel": "0.806",
                        },
                        {
                            "level": "10.0",
                            "position": "75",
                            "micronsPerXPixel": "0.438",
                            "micronsPerYPixel": "0.438",
                        },
                        {
                            "level": "15.0",
                            "position": "90",
                            "micronsPerXPixel": "0.302",
                            "micronsPerYPixel": "0.302",
                        },
                    ]
                },
                "tolerance": "1.0",
            }
        }

    @staticmethod
    def get_display_config():
        return DisplayConfig(
            zoom_levels={
                1.0: DisplayConfigData(
                    crosshairX=477,
                    crosshairY=359,
                    topLeftX=383,
                    topLeftY=253,
                    bottomRightX=410,
                    bottomRightY=278,
                ),
                2.5: DisplayConfigData(
                    crosshairX=493,
                    crosshairY=355,
                    topLeftX=340,
                    topLeftY=283,
                    bottomRightX=388,
                    bottomRightY=322,
                ),
                5.0: DisplayConfigData(
                    crosshairX=517,
                    crosshairY=350,
                    topLeftX=268,
                    topLeftY=326,
                    bottomRightX=354,
                    bottomRightY=387,
                ),
                7.5: DisplayConfigData(
                    crosshairX=549,
                    crosshairY=437,
                    topLeftX=248,
                    topLeftY=394,
                    bottomRightX=377,
                    bottomRightY=507,
                ),
                10.0: DisplayConfigData(
                    crosshairX=613,
                    crosshairY=344,
                    topLeftX=2,
                    topLeftY=489,
                    bottomRightX=206,
                    bottomRightY=630,
                ),
                15.0: DisplayConfigData(
                    crosshairX=693,
                    crosshairY=339,
                    topLeftX=1,
                    topLeftY=601,
                    bottomRightX=65,
                    bottomRightY=767,
                ),
            },
        )
