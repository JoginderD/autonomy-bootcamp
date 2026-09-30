import time

import numpy as np

from .abstract_camera import AbstractCamera
from .frame import CameraFrame


class SimCamera(AbstractCamera):
    """Fake camera that makes up its own frames.

    The docstring at the top of this file says what it has to do, and
    ``tests/test_sim_camera.py`` checks all of it.
    """

    def __init__(self, width: int = 64, height: int = 48) -> None:
        """Save the settings and set up whatever state you need.

        Args:
            width: Frame width in pixels.
            height: Frame height in pixels.
        """
        self._width = width
        self._height = height

        self._initialized = False
        self._captures = 0
        self._last_timestamp = float("-inf")

        # TODO(bootcamper): save the arguments and set up your state
        # (FixedCamera.__init__ shows you what that looks like).

    def initialize_camera(self) -> bool:
        """Turn the fake camera on and start counting from index 0."""
        self._initialized = True
        self._captures = 0
        return True
        # TODO(bootcamper): implement.

    def capture_frame(self) -> CameraFrame:
        if not self._initialized:
            raise RuntimeError(
                "capture_frame() called on a camera that is not initialized; "
                "call initialize_camera() first"
            )

        image = np.full(
            (self._height, self._width, 3),
            self._captures % 256,
            dtype=np.uint8,
        )

        timestamp = time.monotonic()
        if timestamp <= self._last_timestamp:
            timestamp = self._last_timestamp + 1e-6
        self._last_timestamp = timestamp

        frame = CameraFrame(
            rgb=image.copy(),
            timestamp=timestamp,
            index=self._captures,
        )

        self._captures += 1
        return frame

    def stop(self) -> None:
        self._initialized = False