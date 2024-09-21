from json import dumps as json_dumps
import matplotlib.pyplot as plt
from neo4j import GraphDatabase
from neo4j.exceptions import DatabaseError, ClientError
import networkx as nx
import osmnx as ox
import pandas as pd
from shapely.wkt import loads as shapely_loads

BARCELONA_BBOX = (41.45148, 41.34060, 2.05015, 2.23331)


def download_graph(save: bool = True, plot: bool = True):
    graph = ox.graph_from_bbox(bbox=BARCELONA_BBOX, network_type="bike")

    if save:
        ox.save_graphml(graph, "api/data/bycicle_network.graphml")

    if plot:
        _, ax = plt.subplots(figsize=(10, 10))
        ox.plot_graph(
            ox.project_graph(graph),
            ax=ax,
            node_size=0,
            edge_linewidth=0.5,
            edge_color="b",
        )
        plt.title("Bicycle Network")

        plot_name = "api/data/bicycle_network.png"
        plt.savefig(plot_name, dpi=300, bbox_inches="tight")

        plt.close()
    return graph


def graph_to_csv(graph: nx.Graph):
    nodes_dataframe = pd.DataFrame(graph.nodes(data=True), columns=["id", "properties"])
    nodes_dataframe.to_csv("api/data/nodes.csv", index=False)

    edges_dataframe = pd.DataFrame(
        graph.edges(data=True), columns=["source", "target", "attributes"]
    )
    edges_dataframe.to_csv("api/data/edges.csv", index=False)


def generate_merge_queries(graph: nx.Graph):
    """Extract the nodes properties into a dictionary by the node ids
    Loop through the edges and generate MERGE queries (will create if not exist) creating on the fly the nodes and edges
    with the desired attributes/properties"""
    merge_nodes_queries = []
    node_properties_by_node_id = {}
    for node_id, properties in graph.nodes(data=True):
        node_properties_by_node_id[node_id] = ", ".join(
            f"{key}: {json_dumps(value)}"
            for key, value in {
                "id": node_id,
                "latitude": properties["y"],
                "longitude": properties["x"],
            }.items()
        )
    with open("api/data/create_queries.cypherl", "w") as cypherlfile:
        for node_id_1, node_id_2, data in graph.edges(data=True):
            edge_geometry = (
                data["geometry"]
                if "geometry" in data
                else shapely_loads("LINESTRING EMPTY")
            )
            cypherlfile.write(
                f"MERGE (n1:Node {{{node_properties_by_node_id[node_id_1]}}}) "
                f"MERGE (n2:Node {{{node_properties_by_node_id[node_id_2]}}}) "
                f'MERGE (n1)-[:TOWARDS {{geometry: "{edge_geometry.wkt}", distance: {edge_geometry.length}}}]->(n2);\n'
            )
            merge_nodes_queries.append(
                f"MERGE (n1:Node {{{node_properties_by_node_id[node_id_1]}}}) "
                f"MERGE (n2:Node {{{node_properties_by_node_id[node_id_2]}}}) "
                f'MERGE (n1)-[:TOWARDS {{geometry: "{edge_geometry.wkt}", distance: {edge_geometry.length}}}]->(n2) '
            )
    return merge_nodes_queries


def load_graph_to_db(load_data_queries: list[str]):
    with GraphDatabase.driver(
        "bolt://localhost:7687", auth=("memgraph", "memgraph")
    ) as client:
        # Check the connection
        client.verify_connectivity()
        try:
            with client.session() as session:
                with session.begin_transaction() as tx:
                    for query in load_data_queries:
                        tx.run(query)
        except DatabaseError as e:
            print(f"An error occurred: {e}")
            tx.rollback()
            print("Transaction rolled back.")
        except ClientError as e:
            print(f"Query error: {query}")
            print(f"An error occurred: {e}")
            tx.rollback()
            print("Transaction rolled back.")


if __name__ == "__main__":
    bike_graph = download_graph()
    graph_to_csv(bike_graph)
    load_data_queries = generate_merge_queries(bike_graph)
    load_graph_to_db(load_data_queries)
