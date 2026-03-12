import base64
import unittest
from unittest.mock import patch

import numpy as np

import sensors


class SensorsTests(unittest.TestCase):
    def test_capture_stitched_frame_returns_base64_jpeg(self) -> None:
        webcam = np.zeros((sensors.WEBCAM_HEIGHT, sensors.WEBCAM_WIDTH, 3), dtype=np.uint8)
        screen = np.zeros((sensors.SCREEN_HEIGHT, sensors.SCREEN_WIDTH, 3), dtype=np.uint8)

        with (
            patch.object(sensors, "_capture_webcam", return_value=webcam),
            patch.object(sensors, "_capture_screen", return_value=screen),
        ):
            encoded = sensors.capture_stitched_frame()

        self.assertIsNotNone(encoded)
        assert encoded is not None
        decoded = base64.b64decode(encoded)
        self.assertGreater(len(decoded), 0)

    def test_capture_stitched_frame_none_when_no_inputs(self) -> None:
        with (
            patch.object(sensors, "_capture_webcam", return_value=None),
            patch.object(sensors, "_capture_screen", return_value=None),
        ):
            encoded = sensors.capture_stitched_frame()
        self.assertIsNone(encoded)


if __name__ == "__main__":
    unittest.main()
