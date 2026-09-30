from __future__ import annotations

import py_trees

from engine import blackboard_keys


class CaptureForPerception(py_trees.behaviour.Behaviour):
    def __init__(self, name: str, publisher, timeout_ticks: int = 20) -> None:
        super().__init__(name=name)

        self._publisher = publisher
        self._timeout_ticks = timeout_ticks

        self._starting_index = None
        self._ticks = 0

        self.blackboard = self.attach_blackboard_client(name=self.name)
        self.blackboard.register_key(
            key=blackboard_keys.LATEST_FRAME,
            access=py_trees.common.Access.READ,
        )

    def _latest_frame(self):
        try:
            return self.blackboard.get(blackboard_keys.LATEST_FRAME)
        except KeyError:
            return None

    def initialise(self) -> None:
        frame = self._latest_frame()

        if frame is None:
            self._starting_index = None
        else:
            self._starting_index = frame.index

        self._ticks = 0

    def update(self) -> py_trees.common.Status:
        frame = self._latest_frame()

        if frame is not None and frame.index != self._starting_index:
            self._publisher.publish_image(frame)
            self._publisher.publish_status(
                {
                    "phase": "capture",
                    "frame_index": frame.index,
                }
            )

            return py_trees.common.Status.SUCCESS

        self._ticks += 1

        if self._ticks >= self._timeout_ticks:
            return py_trees.common.Status.FAILURE

        return py_trees.common.Status.RUNNING