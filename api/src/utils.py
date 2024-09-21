from neo4j import AsyncGraphDatabase
from pathlib import Path
from shapely import Point, STRtree
from shapely.wkt import loads as load_wkt
import geojson

from contextlib import asynccontextmanager
from typing import Any

from .data_model import Coordinate

# LATITUDE IS THE 41...
# LONGITUDE IS THE 2.....
# LATITUDE IS Y in the nodes.csv


@asynccontextmanager
async def get_async_graph_session(
    uri: str = "bolt://localhost:7687",
    user: str = "memgraph",
    password: str = "memgraph",
):
    client = AsyncGraphDatabase.driver(uri, auth=(user, password))

    await client.verify_connectivity()
    session = client.session()

    try:
        yield session
    finally:
        await session.close()
        await client.close()


async def dq_get_path_between_nodes(start: Point, end: Point) -> Any:
    async with get_async_graph_session() as session:
        async with await session.begin_transaction() as tx:
            result = await tx.run(
                "MATCH (n1:Node {latitude: $start_latitude, longitude: $start_longitude}), "
                "(n2:Node {latitude: $end_latitude, longitude: $end_longitude})"
                'CALL algo.astar(n1, n2, {distance_prop: "distance", latitude_name: "latitude", longitude_name: "longitude"}) '
                "YIELD path RETURN path;",
                start_latitude=start.x,
                start_longitude=start.y,
                end_latitude=end.x,
                end_longitude=end.y,
            )
            record = await result.single()
            if not record:
                return "ERROR NO PATH FOUND"
            path = record["path"]
            coordinate_list = [[node["latitude"], node["longitude"]] for node in path.nodes]       
            geojson_feature = geojson.LineString(coordinates=coordinate_list)

    return geojson.FeatureCollection([geojson_feature])


async def dq_truncate_database() -> None:
    async with get_async_graph_session() as session:
        async with await session.begin_transaction() as tx:
            await tx.run("MATCH (n) DETACH DELETE n")


async def dq_load_graph_from_cypherl_file(path: Path) -> None:
    async with get_async_graph_session() as session:
        async with await session.begin_transaction() as tx:
            with open(path, "r") as queries_file:
                for query in queries_file:
                    await tx.run(query)


def dq_get_nearest_points(
    nodes_strtree: STRtree, start: Coordinate, end: Coordinate
) -> tuple[Point, Point]:
    nearest_start_index = nodes_strtree.nearest(Point(start.lat, start.lon))
    nearest_end_index = nodes_strtree.nearest(Point(end.lat, end.lon))

    nearest_start_point = nodes_strtree.geometries.take(nearest_start_index)
    nearest_end_point = nodes_strtree.geometries.take(nearest_end_index)

    return nearest_start_point, nearest_end_point
