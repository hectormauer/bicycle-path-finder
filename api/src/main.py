from contextlib import asynccontextmanager
from json import loads as json_loads
from pathlib import Path
from shapely import STRtree, Point
# from geopy.distance import geodesic
import csv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .data_model import Coordinate
from .utils import (
    dq_get_nearest_points,
    dq_get_path_between_nodes,
    dq_truncate_database,
    dq_load_graph_from_cypherl_file,
)

origins = [
    "http://localhost",
    "http://localhost:5173/",
    "http://127.0.0.1:5173/",
]

current_dir = Path(__file__).resolve().parent
nodes_csv_file_path = current_dir / "../data/nodes.csv"
nodes_csv_file_path = nodes_csv_file_path.resolve()  # Resolve to an absolute path

load_queries_file_path = current_dir / "../data/create_queries.cypherl"
load_queries_file_path = load_queries_file_path.resolve()  # Resolve to an absolute path


@asynccontextmanager
async def lifespan(app: FastAPI):
    geometries = []
    with open(nodes_csv_file_path, "r") as nodes_csv:
        reader = csv.DictReader(nodes_csv, fieldnames=("id", "properties"))
        for row in reader:
            properties = json_loads(row["properties"].replace("'", '"'))
            geometries.append(
                Point(properties["latitude"], properties["longitude"])
            )  # these are actually lat, lon
    app.state.nodes_strtree = STRtree(geometries)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/truncate-db/")
async def truncate_database():
    await dq_truncate_database()
    return {"status": 200, "message": "Truncated all nodes in the Database"}


@app.post("/load-graph-database/")
async def load_graph_to_database(path: Path = load_queries_file_path):
    await dq_load_graph_from_cypherl_file(path)
    return {"status": 200, "message": "Loaded graph to the database"}


@app.post("/get-path/")
async def get_path(start: Coordinate, end: Coordinate):
    # Find the closest points in our DB to those clicked by the user:
    nearest_start_point, nearest_end_point = dq_get_nearest_points(
        app.state.nodes_strtree, start, end
    )

    # The distances seem quite big (~40/50 meters), maybe due to the nature of just searching nodes and their density?
    # Ideally we'd want a point in the nearest edge, but then not sure how to query the path, since this needs nodes?
    # start_distance = geodesic(
    #     (start.lat, start.lon), (nearest_start_point.x, nearest_start_point.y)
    # ).meters
    # end_distance = geodesic(
    #     (end.lat, end.lon), (nearest_end_point.x, nearest_end_point.y)
    # ).meters

    path = await dq_get_path_between_nodes(nearest_start_point, nearest_end_point)
    return path
