from daq_config_server.models import (
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
                    crosshair_x=477,
                    crosshair_y=359,
                    top_left_x=383,
                    top_left_y=253,
                    bottom_right_x=410,
                    bottom_right_y=278,
                ),
                2.5: DisplayConfigData(
                    crosshair_x=493,
                    crosshair_y=355,
                    top_left_x=340,
                    top_left_y=283,
                    bottom_right_x=388,
                    bottom_right_y=322,
                ),
                5.0: DisplayConfigData(
                    crosshair_x=517,
                    crosshair_y=350,
                    top_left_x=268,
                    top_left_y=326,
                    bottom_right_x=354,
                    bottom_right_y=387,
                ),
                7.5: DisplayConfigData(
                    crosshair_x=549,
                    crosshair_y=437,
                    top_left_x=248,
                    top_left_y=394,
                    bottom_right_x=377,
                    bottom_right_y=507,
                ),
                10.0: DisplayConfigData(
                    crosshair_x=613,
                    crosshair_y=344,
                    top_left_x=2,
                    top_left_y=489,
                    bottom_right_x=206,
                    bottom_right_y=630,
                ),
                15.0: DisplayConfigData(
                    crosshair_x=693,
                    crosshair_y=339,
                    top_left_x=1,
                    top_left_y=601,
                    bottom_right_x=65,
                    bottom_right_y=767,
                ),
            },
        )
