import osmnx as ox
import networkx as nx
from datetime import datetime

def build_graph(lat, lon, transport='drive'):
    dist_dict = {"walk":1500, "bike":2500, "drive":3000, "bus":3000}
    G = ox.graph_from_point((lat, lon), dist=dist_dict.get(transport,2000), network_type=transport)

    now_hour = datetime.now().hour
    congestion_factor = 1.0
    if 7 <= now_hour <= 9 or 17 <= now_hour <= 19:
        congestion_factor = 1.5

    for u,v,d in G.edges(data=True):
        d['weight'] = d.get('length',1) * congestion_factor
    return G

def find_optimal_route(G, start_point, end_point):
    # scikit-learn 필요
    orig = ox.nearest_nodes(G, start_point[1], start_point[0])
    dest = ox.nearest_nodes(G, end_point[1], end_point[0])

    try:
        route = nx.shortest_path(G, orig, dest, weight='weight')
        total_length = nx.shortest_path_length(G, orig, dest, weight='weight')
        return route, total_length
    except:
        return [], 0
