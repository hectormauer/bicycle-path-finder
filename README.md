# Bicyle Path Finder

The following (dev, very much dev) project sets up a web-map UI, using [maplibre-gl](https://maplibre.org/maplibre-gl-js/docs/) and a free (and very nice) `style.json` from [Stadia Maps](https://docs.stadiamaps.com/map-styles/alidade-smooth-dark/). The map is capped to (approximately) Barcelona's Bounding Box for simplicity and performance. 

The UI is then connected to an API, written in Python and using the [FastAPI framework](https://fastapi.tiangolo.com/).

## Requirements
- node > 18 for the UI.
- Python >= 3.12 for the API.
- [rye](https://rye.astral.sh/guide/installation/) to install the Python dependencies.
- Docker as you will probably prefer to use Docker than running `memgraph` locally.
- Installing memgraph and MAGE locally is quite tricky. I recommend the following docker image: `docker run -p 7687:7687 -p 7444:7444 memgraph/memgraph-mage`
- If you still want to run this locally:
    - [memgraph](https://memgraph.com/docs/getting-started/install-memgraph/) to load the bicycle network graph on and run path finding queries.
    - [MAGE (Memgraph Advanced Graph Extensions)](https://github.com/memgraph/mage) (I was not able to install this locally)


## Launch this beautiful map

### UI
On a terminal:
```
cd ui
npm install
npm run dev
```

### API
On a different terminal:
```
cd api
rye sync
source .venv/bin/activate
rye run devserver
```

## Things to consider
### The DATA
I downloaded the graph using the wonderful [osmnx Python Library](https://osmnx.readthedocs.io/en/stable/user-reference.html), which is a very nice and clean wrapper to the [Overpass API](https://overpass-turbo.eu/), which in itself is a wonderful way to interact and download data directly from the wonderful [OpenStreetMap](https://www.openstreetmap.org/#map=13/41.39445/2.15255) (note it's a map in singular, crazy world).

To avoid repeating the job, the downloaded data (Barcelona) is stored in [api/data](api/data). If you wish to generate data for any other specific data, please make use of the script [fetch_graph_data](api/scripts/fetch_graph_data.py). You will then need to manually change the hardcoded bounding box (top of the file, `BARCELONA_BBOX = (41.45148, 41.34060, 2.05015, 2.23331)`) and execute it:

```
cd api
source .venv/bin/activate
rye run downloadgraph
```

This should create a set of files, which are necessary for the API to work and for the loading process:

1. nodes.csv: a CSV with the nodes that form the graph.
2. edges.csv: a CSV with the edges that form the graph.
3. create_queries.cypherl: A file containing the Cypher queries needed to load/create such graph in memgraph.
4. If the script is executed with `save=True` (default) a `bycicle_network.graphml` will be saved. I have not used it, but it might be handy if one wants to visualise the graph without loading it to a DB.
5. If the script is executed with `plot=True` (default) a `bicycle_network.png` image will be saved. It is nice to visualize <3.

I don't fully understand why someone would want something different to the beautiful Barcelona cycling network, but we're living strange times:

![Barcelona Cycle Network](api/data/bicycle_network_barcelona.png)

### The LOADING TIME
It takes a long time to load this onto the Graph DB. We have similar issues currently with the Graph Service. 

It can be done in different ways, ordered here from more to less performant:

1. Using the memgraph cli: `mgconsole < path/to/create_queries.cypherl`
2. Using the API endpoint: `curl -X 'POST' 'http://127.0.0.1:3000/load-graph-database/' -H 'accept: application/json' -d ''`
3. Using the given script (`rye run downloadgraph`) it ends up loading it into the DB.

### Tests

![tests](api/data/hop-on-the-cycle-frontier.gif)

Nah, really, I just did not have time to work on them. I will add some in the future.


### BUT DOES IT WORK?

Sometimes, hehe. And I guess it is as good as the data :D

![live-test](api/data/testing-the-ui.gif)