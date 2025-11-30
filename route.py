# route.py
import osmnx as ox
import networkx as nx
from datetime import datetime

def build_graph(lat, lon, transport='drive'):
    G = ox.graph_from_point((lat, lon), dist=5000, network_type=transport)
    now_hour = datetime.now().hour
    congestion_factor = 1.0
    if 7 <= now_hour <= 9 or 17 <= now_hour <= 19:
        congestion_factor = 1.5
    for u, v, data in G.edges(data=True):
        data['weight'] = data.get('length', 1) * congestion_factor
    return G

def find_optimal_route(G, start_point, end_point):
    # 최신 OSMnx 사용법
    orig_node = ox.distance.nearest_nodes(G, X=start_point[1], Y=start_point[0])
    dest_node = ox.distance.nearest_nodes(G, X=end_point[1], Y=end_point[0])
    
    try:
        route = nx.shortest_path(G, orig_node, dest_node, weight='weight')
        total_length = nx.shortest_path_length(G, orig_node, dest_node, weight='weight')
        return route, total_length
    except:
        return [], 0
