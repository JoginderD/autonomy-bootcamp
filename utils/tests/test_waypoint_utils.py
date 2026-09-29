import dataclasses

import pytest

from src.types import Coordinate
from src.waypoint_utils import (
    east_north_coordinate_offset_m,
    parse_waypoints_file,
    sort_clockwise_sweep,
)


def write_to_tmp_waypoints_file(tmp_path, text):
    """Write ``text`` to a YAML file and hand back its path."""
    path = tmp_path / "waypoints.yaml"
    path.write_text(text)
    return path


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            """
            home: {lat: 1, lon: 2, alt: 3}
            waypoints:
              - {lat: 4, lon: 5, alt: 6}
            """,
            (Coordinate(1, 2, 3), [Coordinate(4, 5, 6)]),
        ),
        (
            """
            waypoints:
              - {lat: 4, lon: 5, alt: 6}
              - {lat: 7, lon: 8, alt: 9}
            """,
            (None, [Coordinate(4, 5, 6), Coordinate(7, 8, 9)]),
        ),
        (
            """
            # a lap

            home: {lat: 1, lon: 2, alt: 3}

            waypoints:
              # first leg
              - {lat: 4, lon: 5, alt: 6}
            """,
            (Coordinate(1, 2, 3), [Coordinate(4, 5, 6)]),
        ),
    ],
    ids=["home-and-waypoints", "no-home", "comments-and-blank-lines"],
)
def test_parse_waypoints_file_success(tmp_path, text, expected):
    path = write_to_tmp_waypoints_file(tmp_path, text)
    assert parse_waypoints_file(path) == expected


def test_parse_empty_file(tmp_path):
    path = write_to_tmp_waypoints_file(tmp_path, "")

    assert parse_waypoints_file(path) == (None, [])


def test_parse_empty_waypoints_list(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        waypoints: []
        """,
    )

    assert parse_waypoints_file(path) == (None, [])


def test_parse_top_level_must_be_mapping(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        - one
        - two
        """,
    )

    with pytest.raises(ValueError):
        parse_waypoints_file(path)


@pytest.mark.parametrize("missing_key", ["lat", "lon", "alt"])
def test_parse_waypoint_missing_required_key(tmp_path, missing_key):
    values = {
        "lat": 43.0,
        "lon": -80.0,
        "alt": 10.0,
    }
    del values[missing_key]

    text = f"""
    waypoints:
      - {values}
    """

    path = write_to_tmp_waypoints_file(tmp_path, text)

    with pytest.raises(ValueError):
        parse_waypoints_file(path)


@pytest.mark.parametrize(
    "bad_value",
    ["hello", "not-a-number"],
)
def test_parse_rejects_non_numeric_values(tmp_path, bad_value):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        f"""
        waypoints:
          - {{lat: {bad_value}, lon: -80, alt: 10}}
        """,
    )

    with pytest.raises(ValueError):
        parse_waypoints_file(path)


def test_parse_invalid_yaml(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        waypoints:
          - {lat: 43, lon: -80, alt:
        """,
    )

    with pytest.raises(ValueError):
        parse_waypoints_file(path)


def test_parse_missing_file(tmp_path):
    missing_path = tmp_path / "does_not_exist.yaml"

    with pytest.raises(OSError):
        parse_waypoints_file(missing_path)


@pytest.mark.parametrize(
    ("lat", "lon"),
    [
        (90.1, 0),
        (-90.1, 0),
        (0, 180.1),
        (0, -180.1),
    ],
)
def test_parse_rejects_out_of_range_coordinates(tmp_path, lat, lon):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        f"""
        waypoints:
          - {{lat: {lat}, lon: {lon}, alt: 10}}
        """,
    )

    with pytest.raises(ValueError):
        parse_waypoints_file(path)


def test_coordinate_objects_are_frozen(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        waypoints:
          - {lat: 43, lon: -80, alt: 10}
        """,
    )

    _, waypoints = parse_waypoints_file(path)

    with pytest.raises(dataclasses.FrozenInstanceError):
        waypoints[0].lat = 50


def test_east_offset_at_equator():
    east, north = east_north_coordinate_offset_m(
        0.0,
        0.0,
        0.0,
        1.0,
    )

    assert east == pytest.approx(111195.08, abs=1.0)
    assert north == pytest.approx(0.0, abs=0.01)


def test_north_offset():
    east, north = east_north_coordinate_offset_m(
        0.0,
        0.0,
        1.0,
        0.0,
    )

    assert east == pytest.approx(0.0, abs=0.01)
    assert north == pytest.approx(111195.08, abs=1.0)


def test_east_offset_scales_with_latitude():
    east, north = east_north_coordinate_offset_m(
        60.0,
        0.0,
        60.0,
        1.0,
    )

    assert east == pytest.approx(55597.54, abs=1.0)
    assert north == pytest.approx(0.0, abs=0.01)


def test_sort_empty_list():
    assert sort_clockwise_sweep([]) == []


def test_sort_single_waypoint():
    point = Coordinate(43.0, -80.0, 10.0)

    assert sort_clockwise_sweep([point]) == [point]


def test_sort_clockwise_from_north():
    north = Coordinate(1, 0, 0)
    east = Coordinate(0, 1, 0)
    south = Coordinate(-1, 0, 0)
    west = Coordinate(0, -1, 0)

    waypoints = [south, west, north, east]

    result = sort_clockwise_sweep(waypoints)

    assert result == [north, east, south, west]


def test_sort_starts_in_home_direction():
    north = Coordinate(1, 0, 0)
    east = Coordinate(0, 1, 0)
    south = Coordinate(-1, 0, 0)
    west = Coordinate(0, -1, 0)

    home = Coordinate(0, 2, 0)

    result = sort_clockwise_sweep(
        [north, east, south, west],
        home=home,
    )

    assert result == [east, south, west, north]


def test_home_at_centroid_starts_from_north():
    north = Coordinate(1, 0, 0)
    east = Coordinate(0, 1, 0)
    south = Coordinate(-1, 0, 0)
    west = Coordinate(0, -1, 0)

    home = Coordinate(0, 0, 0)

    result = sort_clockwise_sweep(
        [south, west, north, east],
        home=home,
    )

    assert result == [north, east, south, west]


def test_same_direction_closer_waypoint_first():
    near_north = Coordinate(1, 0, 0)
    far_north = Coordinate(2, 0, 0)
    east = Coordinate(0, 1, 0)
    south = Coordinate(-1, 0, 0)
    west = Coordinate(0, -1, 0)

    result = sort_clockwise_sweep(
        [far_north, east, west, near_north, south]
    )

    assert result.index(near_north) < result.index(far_north)