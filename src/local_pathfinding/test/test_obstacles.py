import pickle
from typing import Any, List

import numpy as np
import pytest
from custom_interfaces.msg import (
    HelperAISShip,
    HelperDimension,
    HelperHeading,
    HelperLatLon,
    HelperROT,
    HelperSpeed,
)
from shapely.geometry import MultiPolygon, Point, Polygon, box

from local_pathfinding.coord_systems import XY, latlon_to_xy, meters_to_km
from local_pathfinding.obstacles import BOAT_BUFFER, Boat, Land, Obstacle


def load_pkl(file_path: str) -> Any:
    with open(file_path, "rb") as f:
        return pickle.load(f)


LAND = load_pkl("/workspaces/sailbot_workspace/src/local_pathfinding/land/pkl/land.pkl")

# LAND OBSTACLES ----------------------------------------------------------------------------------
"""Test Plan
Create Land OK
Pass custom bbox OK
isValid OK
update collision zone OK
update sailbot data OK
update ref point OK
latlon polys to xy polys OK
"""


@pytest.mark.parametrize(
    "reference_point, sailbot_position, next_waypoint, all_land_data, bbox_buffer_amount, land_present",  # noqa
    [
        (
            HelperLatLon(latitude=48.927646856442834, longitude=-125.18555198866946),
            HelperLatLon(latitude=48.842045056421135, longitude=-125.29181185529734),
            HelperLatLon(latitude=48.92893492027311, longitude=-125.37140872956104),
            LAND,
            0.1,  # degrees
            True,
        ),
        (
            HelperLatLon(latitude=44.112832, longitude=-156.008729),
            HelperLatLon(latitude=44.112832, longitude=-151.260136),
            HelperLatLon(latitude=46.097615, longitude=-156.800161),
            LAND,
            0.1,  # degrees
            False,
        ),
    ],
)
def test_create_land(
    reference_point: HelperLatLon,
    sailbot_position: HelperLatLon,
    next_waypoint: HelperLatLon,
    all_land_data: MultiPolygon,
    bbox_buffer_amount: float,
    land_present: bool,
):
    land = Land(
        reference=reference_point,
        sailbot_position=sailbot_position,
        next_waypoint=next_waypoint,
        all_land_data=all_land_data,
        bbox_buffer_amount=bbox_buffer_amount,
    )

    assert isinstance(land.collision_zone, MultiPolygon)
    if land_present:
        assert len(land.collision_zone.geoms) != 0  # type: ignore
    else:
        assert len(land.collision_zone.geoms) == 0  # type: ignore


# Test is_valid
@pytest.mark.parametrize(
    "reference_point, sailbot_position, next_waypoint, all_land_data, bbox_buffer_amount, invalid_point, valid_point, mock_land",  # noqa
    [
        (
            HelperLatLon(latitude=52.26, longitude=-136.91),
            HelperLatLon(latitude=51.95, longitude=-136.26),
            HelperLatLon(latitude=51.96, longitude=-136.27),
            LAND,
            0.1,  # degrees
            XY(0.5, 0.5),
            XY(5, 5),
            MultiPolygon(
                [
                    Polygon([Point([0, 0]), Point([0, 1]), Point([1, 1]), Point([1, 0])]),
                    Polygon([Point([0, 0]), Point([0, 1]), Point([2, 1]), Point([2, 0])]),
                    Polygon([Point([2, 2]), Point([2, 3]), Point([3, 3]), Point([3, 2])]),
                ]
            ),
        )
    ],
)
def test_is_valid_land(
    reference_point: HelperLatLon,
    sailbot_position: HelperLatLon,
    next_waypoint: HelperLatLon,
    all_land_data: MultiPolygon,
    bbox_buffer_amount: float,
    invalid_point: XY,
    valid_point: XY,
    mock_land: MultiPolygon,
):
    land = Land(
        reference=reference_point,
        sailbot_position=sailbot_position,
        next_waypoint=next_waypoint,
        all_land_data=all_land_data,
        bbox_buffer_amount=bbox_buffer_amount,
    )

    land.update_collision_zone(land_multi_polygon=mock_land)
    assert land.is_valid(valid_point)
    assert not land.is_valid(invalid_point)


# Test land collision zone is created/updated successfully
@pytest.mark.parametrize(
    "reference_point, sailbot_position, next_waypoint, all_land_data, bbox_buffer_amount",
    [
        (
            HelperLatLon(latitude=48.927646856442834, longitude=-125.18555198866946),
            HelperLatLon(latitude=48.842045056421135, longitude=-125.29181185529734),
            HelperLatLon(latitude=48.92893492027311, longitude=-125.37140872956104),
            LAND,
            0.1,  # degrees
        )
    ],
)
def test_land_collision_zone(
    reference_point: HelperLatLon,
    sailbot_position: HelperLatLon,
    next_waypoint: HelperLatLon,
    all_land_data: MultiPolygon,
    bbox_buffer_amount,
):
    land = Land(
        reference=reference_point,
        sailbot_position=sailbot_position,
        next_waypoint=next_waypoint,
        all_land_data=all_land_data,
        bbox_buffer_amount=bbox_buffer_amount,
    )
    land.update_collision_zone()

    assert isinstance(land.collision_zone, MultiPolygon)
    assert len(land.collision_zone.geoms) != 0


# Test passing a custom bbox to update_collision_zone works as well
@pytest.mark.parametrize(
    "reference_point, sailbot_position, next_waypoint, all_land_data, bbox_buffer_amount, valid_point, invalid_point",  # noqa
    [
        (
            HelperLatLon(latitude=49.155485, longitude=-126.987704),
            HelperLatLon(latitude=48.838328, longitude=-126.380390),
            HelperLatLon(latitude=49.155485, longitude=-126.987704),
            LAND,
            0.1,  # degrees
            HelperLatLon(latitude=48.955695, longitude=-126.743129),
            HelperLatLon(latitude=49.159077, longitude=-126.322681),
        )
    ],
)
def test_custom_state_space_passed_to_update_collision_zone(
    reference_point: HelperLatLon,
    sailbot_position: HelperLatLon,
    next_waypoint: HelperLatLon,
    all_land_data: MultiPolygon,
    bbox_buffer_amount: float,
    valid_point: HelperLatLon,
    invalid_point: HelperLatLon,
):
    land = Land(
        reference=reference_point,
        sailbot_position=sailbot_position,
        next_waypoint=next_waypoint,
        all_land_data=all_land_data,
        bbox_buffer_amount=bbox_buffer_amount,
    )

    sailbot_box = Point(sailbot_position.longitude, sailbot_position.latitude).buffer(
        bbox_buffer_amount, cap_style=3, join_style=2
    )
    # create a box around the next waypoint
    waypoint_box = Point(next_waypoint.longitude, next_waypoint.latitude).buffer(
        bbox_buffer_amount, cap_style=3, join_style=2
    )
    # create a bounding box around both boxes
    custom_state_space = box(*MultiPolygon([sailbot_box, waypoint_box]).bounds)

    land.update_collision_zone(state_space=custom_state_space)

    assert isinstance(land.collision_zone, MultiPolygon)
    assert len(land.collision_zone.geoms) != 0

    valid_xy = latlon_to_xy(reference_point, valid_point)
    invalid_xy = latlon_to_xy(reference_point, invalid_point)

    assert land.is_valid(valid_xy)
    assert not land.is_valid(invalid_xy)


# Test updating Sailbot data
@pytest.mark.parametrize(
    "reference_point, sailbot_position_1, sailbot_position_2, next_waypoint, all_land_data, bbox_buffer_amount",  # noqa
    [
        (
            HelperLatLon(latitude=52.26, longitude=-136.91),
            HelperLatLon(latitude=51.0, longitude=-136.0),
            HelperLatLon(latitude=52.0, longitude=-137.0),
            HelperLatLon(latitude=53.0, longitude=-138.0),
            LAND,
            0.1,  # degrees
        )
    ],
)
def test_update_sailbot_data_land(
    reference_point: HelperLatLon,
    sailbot_position_1: HelperLatLon,
    sailbot_position_2: HelperLatLon,
    next_waypoint: HelperLatLon,
    all_land_data: MultiPolygon,
    bbox_buffer_amount,
):
    land = Land(
        reference=reference_point,
        sailbot_position=sailbot_position_1,
        next_waypoint=next_waypoint,
        all_land_data=all_land_data,
        bbox_buffer_amount=bbox_buffer_amount,
    )

    land.update_sailbot_data(sailbot_position_2)
    assert land.sailbot_position == pytest.approx(
        latlon_to_xy(reference_point, sailbot_position_2)
    )


# Test update reference point
@pytest.mark.parametrize(
    "reference_point_1,reference_point_2,sailbot_position,next_waypoint,all_land_data,bbox_buffer_amount",  # noqa
    [
        (
            HelperLatLon(latitude=52.2, longitude=-136.9),
            HelperLatLon(latitude=51.0, longitude=-136.0),
            HelperLatLon(latitude=51.95785651405779, longitude=-136.26282894969611),
            HelperLatLon(latitude=50.06442134644842, longitude=-130.7725487868677),
            LAND,
            0.1,  # degrees
        ),
    ],
)
def test_update_reference_point_land(
    reference_point_1: HelperLatLon,
    reference_point_2: HelperLatLon,
    sailbot_position: HelperLatLon,
    next_waypoint: HelperLatLon,
    all_land_data: MultiPolygon,
    bbox_buffer_amount,
):
    land = Land(
        reference=reference_point_1,
        sailbot_position=sailbot_position,
        next_waypoint=next_waypoint,
        all_land_data=all_land_data,
        bbox_buffer_amount=bbox_buffer_amount,
    )

    if isinstance(land.collision_zone, MultiPolygon):
        point1 = Point(
            land.collision_zone.geoms[0].exterior.coords.xy[0][0],
            land.collision_zone.geoms[0].exterior.coords.xy[1][0],
        )

    assert land.reference == reference_point_1

    assert land.sailbot_position == pytest.approx(
        latlon_to_xy(reference_point_1, sailbot_position)
    )

    # Change the reference point
    land.update_reference_point(reference_point_2)

    if isinstance(land.collision_zone, MultiPolygon):
        point2 = Point(
            land.collision_zone.geoms[0].exterior.coords.xy[0][0],
            land.collision_zone.geoms[0].exterior.coords.xy[1][0],
        )

    assert land.reference == reference_point_2
    assert land.sailbot_position_latlon == sailbot_position
    assert land.sailbot_position == pytest.approx(
        latlon_to_xy(reference_point_2, sailbot_position)
    )

    # Calculate the expected displacement based on the old and new reference point
    x_displacement, y_displacement = latlon_to_xy(reference_point_2, reference_point_1)
    displacement = np.sqrt(x_displacement**2 + y_displacement**2)
    # calculate how far the collision zone was actually translated on reference point update
    translation = point1.distance(point2)

    # There is some error in the latlon_to_xy conversion but the results are close
    assert translation == pytest.approx(displacement, rel=0.1), "incorrect translation"


# Test latlon polygons to xy polygons
# just asserts that every point in every xy_polygon agrees with latlon_to_xy() from coord_systems
@pytest.mark.parametrize(
    "latlon_polygons, reference_point",
    [
        (
            list(
                [
                    Polygon(
                        [
                            (-129.10434, 49.173085),
                            (-131.23681, 50.112124),
                            (-134.820239, 50.658515),
                            (-135.963419, 49.772751),
                            (-136.359135, 48.230528),
                            (-134.556428, 47.671306),
                            (-131.478636, 47.78954),
                            (-129.895772, 48.274419),
                            (-129.412119, 48.928274),
                        ]
                    ),
                    Polygon(
                        [
                            (-123.872094, 50.252825),
                            (-124.135905, 49.530913),
                            (-125.938612, 49.758558),
                            (-125.674801, 50.797603),
                        ]
                    ),
                    Polygon(
                        [
                            (-123.872094, 50.252825),
                            (-124.135905, 49.530913),
                            (-125.938612, 49.758558),
                            (-125.674801, 50.797603),
                        ]
                    ),
                ]
            ),
            HelperLatLon(latitude=51.527884, longitude=-132.643800),
        ),
        (
            list(
                [
                    Polygon(
                        [
                            (-123.872094, 50.252825),
                            (-124.135905, 49.530913),
                            (-125.938612, 49.758558),
                            (-125.674801, 50.797603),
                        ]
                    ),
                ]
            ),
            HelperLatLon(latitude=51.527884, longitude=-132.643800),
        ),
        (
            list([]),
            HelperLatLon(latitude=51.527884, longitude=-132.643800),
        ),
    ],
)
def test_latlon_polygons_to_xy_polygons(
    latlon_polygons: List[Polygon], reference_point: HelperLatLon
):

    xy_polygons = Land._latlon_polygons_to_xy_polygons(latlon_polygons, reference_point)
    assert isinstance(xy_polygons, list)
    assert len(xy_polygons) == len(latlon_polygons)

    if len(xy_polygons) > 0:
        for i, xy_poly in enumerate(xy_polygons):
            latlon_poly = latlon_polygons[i]
            assert isinstance(xy_poly, Polygon)
            assert xy_poly.exterior.coords is not None

            for j, xy_point in enumerate(xy_poly.exterior.coords):
                latlon_point = latlon_poly.exterior.coords[j]
                assert isinstance(xy_point, tuple)
                assert xy_point == pytest.approx(
                    latlon_to_xy(
                        reference_point,
                        HelperLatLon(longitude=latlon_point[0], latitude=latlon_point[1]),
                    )
                )


# BOAT OBSTACLES ----------------------------------------------------------------------------------
"""Test Plan
isValid OK
update collision zone OK
update sailbot data OK
update ref point OK
init OK
calc proj dist OK
"""


# Test calculate projected distance
# Boat and Sailbot in same location
@pytest.mark.parametrize(
    "reference_point,sailbot_position,ais_ship,sailbot_speed",
    [
        (
            HelperLatLon(latitude=52.268119490007756, longitude=-136.9133983613776),
            HelperLatLon(latitude=51.957, longitude=-136.262),
            HelperAISShip(
                id=1,
                lat_lon=HelperLatLon(latitude=51.957, longitude=-136.262),
                cog=HelperHeading(heading=30.0),
                sog=HelperSpeed(speed=20.0),
                width=HelperDimension(dimension=20.0),
                length=HelperDimension(dimension=100.0),
                rot=HelperROT(rot=0),
            ),
            15.0,
        )
    ],
)
def test_calculate_projected_distance(
    reference_point: HelperLatLon,
    sailbot_position: HelperLatLon,
    ais_ship: HelperAISShip,
    sailbot_speed: float,
):
    boat1 = Boat(reference_point, sailbot_position, sailbot_speed, ais_ship)

    assert boat1._calculate_projected_distance() == pytest.approx(
        0.0
    ), "incorrect projected distance"


# Test collision zone is created successfully
@pytest.mark.parametrize(
    "reference_point,sailbot_position,ais_ship,sailbot_speed",
    [
        (
            HelperLatLon(latitude=52.268119490007756, longitude=-136.9133983613776),
            HelperLatLon(latitude=51.95785651405779, longitude=-136.26282894969611),
            HelperAISShip(
                id=1,
                lat_lon=HelperLatLon(latitude=51.97917631092298, longitude=-137.1106454702385),
                cog=HelperHeading(heading=30.0),
                sog=HelperSpeed(speed=20.0),
                width=HelperDimension(dimension=20.0),
                length=HelperDimension(dimension=100.0),
                rot=HelperROT(rot=0),
            ),
            15.0,
        )
    ],
)
def test_boat_collision_zone(
    reference_point: HelperLatLon,
    sailbot_position: HelperLatLon,
    ais_ship: HelperAISShip,
    sailbot_speed: float,
):
    boat1 = Boat(reference_point, sailbot_position, sailbot_speed, ais_ship)
    boat1._update_boat_collision_zone()

    assert isinstance(boat1.collision_zone, Polygon)
    if boat1.collision_zone is not None:
        assert boat1.collision_zone.exterior.coords is not None


# Test collision zone is positioned correctly
# ais_ship is positioned at the reference point
@pytest.mark.parametrize(
    "reference_point,sailbot_position,ais_ship,sailbot_speed",
    [
        (
            HelperLatLon(latitude=52.0, longitude=-136.0),
            HelperLatLon(latitude=51.95785651405779, longitude=-136.26282894969611),
            HelperAISShip(
                id=1,
                lat_lon=HelperLatLon(latitude=52.0, longitude=-136.0),
                cog=HelperHeading(heading=0.0),
                sog=HelperSpeed(speed=20.0),
                width=HelperDimension(dimension=20.0),
                length=HelperDimension(dimension=100.0),
                rot=HelperROT(rot=0),
            ),
            15.0,
        )
    ],
)
def test_position_collision_zone(
    reference_point: HelperLatLon,
    sailbot_position: HelperLatLon,
    ais_ship: HelperAISShip,
    sailbot_speed: float,
):
    boat1 = Boat(reference_point, sailbot_position, sailbot_speed, ais_ship)

    if boat1.collision_zone is not None:
        unbuffered = boat1.collision_zone.buffer(-BOAT_BUFFER, join_style=2)
        x, y = np.array(unbuffered.exterior.coords.xy)
        x = np.array(x)
        y = np.array(y)
        assert (x[0] + meters_to_km(boat1.ais_ship.width.dimension) / 2) == pytest.approx(0)
        assert (y[0] + meters_to_km(boat1.ais_ship.length.dimension) / 2) == pytest.approx(0)


# Test create collision zone raises error when id of passed ais_ship does not match self's id
@pytest.mark.parametrize(
    "reference_point,sailbot_position,ais_ship_1,ais_ship_2,sailbot_speed",
    [
        (
            HelperLatLon(latitude=52.268119490007756, longitude=-136.9133983613776),
            HelperLatLon(latitude=51.95785651405779, longitude=-136.26282894969611),
            HelperAISShip(
                id=1,
                lat_lon=HelperLatLon(latitude=51.97917631092298, longitude=-137.1106454702385),
                cog=HelperHeading(heading=30.0),
                sog=HelperSpeed(speed=20.0),
                width=HelperDimension(dimension=20.0),
                length=HelperDimension(dimension=100.0),
                rot=HelperROT(rot=0),
            ),
            HelperAISShip(
                id=2,
                lat_lon=HelperLatLon(latitude=51.97917631092298, longitude=-137.1106454702385),
                cog=HelperHeading(heading=30.0),
                sog=HelperSpeed(speed=20.0),
                width=HelperDimension(dimension=20.0),
                length=HelperDimension(dimension=100.0),
                rot=HelperROT(rot=0),
            ),
            15.0,
        )
    ],
)
def test_create_collision_zone_id_mismatch(
    reference_point: HelperLatLon,
    sailbot_position: HelperLatLon,
    ais_ship_1: HelperAISShip,
    ais_ship_2: HelperAISShip,
    sailbot_speed: float,
):
    boat1 = Boat(reference_point, sailbot_position, sailbot_speed, ais_ship_1)

    with pytest.raises(ValueError):
        boat1._update_boat_collision_zone(ais_ship_2)


# Test is_valid
@pytest.mark.parametrize(
    "reference_point,sailbot_position,ais_ship,sailbot_speed,invalid_point,valid_point",
    [
        (
            HelperLatLon(latitude=52.268119490007756, longitude=-136.9133983613776),
            HelperLatLon(latitude=51.95785651405779, longitude=-136.26282894969611),
            HelperAISShip(
                lat_lon=HelperLatLon(latitude=51.97917631092298, longitude=-137.1106454702385),
                cog=HelperHeading(heading=0.0),
                sog=HelperSpeed(speed=20.0),
                width=HelperDimension(dimension=20.0),
                length=HelperDimension(dimension=100.0),
                rot=HelperROT(rot=0),
            ),
            15.0,
            latlon_to_xy(
                HelperLatLon(latitude=52.268119490007756, longitude=-136.9133983613776),
                HelperLatLon(latitude=52.174842845359755, longitude=-137.10372451905042),
            ),
            latlon_to_xy(
                HelperLatLon(latitude=52.268119490007756, longitude=-136.9133983613776),
                HelperLatLon(latitude=49.30499213908291, longitude=-123.31330140816111),
            ),
        )
    ],
)
def test_is_valid_boat(
    reference_point: HelperLatLon,
    sailbot_position: HelperLatLon,
    ais_ship: HelperAISShip,
    sailbot_speed: float,
    invalid_point: XY,
    valid_point: XY,
):
    boat1 = Boat(reference_point, sailbot_position, sailbot_speed, ais_ship)
    assert not boat1.is_valid(invalid_point)
    assert boat1.is_valid(valid_point)


# Test is_valid raises error when collision zone has not been set
@pytest.mark.parametrize(
    "reference_point,sailbot_position,invalid_point,valid_point",
    [
        (
            HelperLatLon(latitude=52.268119490007756, longitude=-136.9133983613776),
            HelperLatLon(latitude=51.95785651405779, longitude=-136.26282894969611),
            latlon_to_xy(
                HelperLatLon(latitude=52.268119490007756, longitude=-136.9133983613776),
                HelperLatLon(latitude=52.174842845359755, longitude=-137.10372451905042),
            ),
            latlon_to_xy(
                HelperLatLon(latitude=52.268119490007756, longitude=-136.9133983613776),
                HelperLatLon(latitude=49.30499213908291, longitude=-123.31330140816111),
            ),
        )
    ],
)
def test_is_valid_no_collision_zone(
    reference_point: HelperLatLon,
    sailbot_position: HelperLatLon,
    invalid_point: XY,
    valid_point: XY,
):
    obstacle = Obstacle(reference_point, sailbot_position)
    with pytest.raises(RuntimeError):
        obstacle.is_valid(invalid_point)
    with pytest.raises(RuntimeError):
        obstacle.is_valid(valid_point)


# Test updating Sailbot data
@pytest.mark.parametrize(
    "ref_point,sailbot_position_1,sailbot_speed_1,sailbot_position_2,sailbot_speed_2,ais_ship",
    [
        (
            HelperLatLon(latitude=52.268119490007756, longitude=-136.9133983613776),
            HelperLatLon(latitude=51.9, longitude=-136.2),
            15.0,
            HelperLatLon(latitude=52.9, longitude=-137.2),
            20.0,
            HelperAISShip(
                id=1,
                lat_lon=HelperLatLon(latitude=51.97917631092298, longitude=-137.1106454702385),
                cog=HelperHeading(heading=30.0),
                sog=HelperSpeed(speed=20.0),
                width=HelperDimension(dimension=20.0),
                length=HelperDimension(dimension=100.0),
                rot=HelperROT(rot=0),
            ),
        )
    ],
)
def test_update_sailbot_data(
    ref_point: HelperLatLon,
    sailbot_position_1: HelperLatLon,
    sailbot_speed_1: float,
    sailbot_position_2: HelperLatLon,
    sailbot_speed_2: float,
    ais_ship: HelperAISShip,
):
    boat1 = Boat(ref_point, sailbot_position_1, sailbot_speed_1, ais_ship)
    boat1.update_sailbot_data(sailbot_position_2, sailbot_speed_2)

    assert boat1.sailbot_position == pytest.approx(latlon_to_xy(ref_point, sailbot_position_2))
    assert boat1.sailbot_speed == pytest.approx(sailbot_speed_2)


# Test update reference point
@pytest.mark.parametrize(
    "reference_point_1,reference_point_2,sailbot_position,ais_ship,sailbot_speed",
    [
        (
            HelperLatLon(latitude=52.2, longitude=-136.9),
            HelperLatLon(latitude=51.0, longitude=-136.0),
            HelperLatLon(latitude=51.95785651405779, longitude=-136.26282894969611),
            HelperAISShip(
                id=1,
                lat_lon=HelperLatLon(latitude=51.97917631092298, longitude=-137.1106454702385),
                cog=HelperHeading(heading=30.0),
                sog=HelperSpeed(speed=20.0),
                width=HelperDimension(dimension=20.0),
                length=HelperDimension(dimension=100.0),
                rot=HelperROT(rot=0),
            ),
            15.0,
        ),
        (
            HelperLatLon(latitude=50.06442134644842, longitude=-130.7725487868677),
            HelperLatLon(latitude=49.88670956993386, longitude=-130.37061359404225),
            HelperLatLon(latitude=51.95785651405779, longitude=-136.26282894969611),
            HelperAISShip(
                id=1,
                lat_lon=HelperLatLon(latitude=51.97917631092298, longitude=-137.1106454702385),
                cog=HelperHeading(heading=30.0),
                sog=HelperSpeed(speed=20.0),
                width=HelperDimension(dimension=20.0),
                length=HelperDimension(dimension=100.0),
                rot=HelperROT(rot=0),
            ),
            15.0,
        ),
    ],
)
def test_update_reference_point(
    reference_point_1: HelperLatLon,
    reference_point_2: HelperLatLon,
    sailbot_position: HelperLatLon,
    ais_ship: HelperAISShip,
    sailbot_speed: float,
):
    boat1 = Boat(reference_point_1, sailbot_position, sailbot_speed, ais_ship)
    if isinstance(boat1.collision_zone, Polygon):
        point1 = Point(
            boat1.collision_zone.exterior.coords.xy[0][0],
            boat1.collision_zone.exterior.coords.xy[1][0],
        )

    assert boat1.reference == reference_point_1
    assert boat1.sailbot_position == pytest.approx(
        latlon_to_xy(reference_point_1, sailbot_position)
    )
    # Change the reference point
    boat1.update_reference_point(reference_point_2)
    if isinstance(boat1.collision_zone, Polygon):
        point2 = Point(
            boat1.collision_zone.exterior.coords.xy[0][0],
            boat1.collision_zone.exterior.coords.xy[1][0],
        )

    assert boat1.reference == reference_point_2
    assert boat1.sailbot_position_latlon == sailbot_position
    assert boat1.sailbot_position == pytest.approx(
        latlon_to_xy(reference_point_2, sailbot_position)
    )

    # Calculate the expected displacement based on the old and new reference point
    x_displacement, y_displacement = latlon_to_xy(reference_point_2, reference_point_1)
    displacement = np.sqrt(x_displacement**2 + y_displacement**2)
    # calculate how far the collision zone was actually translated on reference point update
    translation = point1.distance(point2)

    # There is some error in the latlon_to_xy conversion but the results are close
    assert translation == pytest.approx(displacement, rel=0.1), "incorrect translation"
