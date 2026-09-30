from __future__ import annotations

from collections.abc import Callable

import py_trees


def create_perception_sweep(
    waypoint_count: int,
    fly_factory: Callable[[int], py_trees.behaviour.Behaviour],
    capture_factory: Callable[[int], py_trees.behaviour.Behaviour],
) -> py_trees.behaviour.Behaviour:
    """
    Builds the part of the tree that visits every waypoint in order.
    """
    sweep = py_trees.composites.Sequence(
        name="PerceptionSweep",
        memory=True,
    )

    children = []

    for index in range(waypoint_count):
        children.append(fly_factory(index))
        children.append(capture_factory(index))

    sweep.add_children(children)

    return sweep