import osmnx as ox
import networkx as nx
from datetime import datetime

def build_graph(lat, lon, transport='drive'):
    """
    lat, lon: 출발지 기준 좌표
    transport: 'walk', 'bike', 'drive'
    """
    # 반경 5km 도로망 가져오기
    G = ox.graph_from_point((lat, lon), dist=5000, network_type=transport)
    
    # 시간대별 혼잡 가중치
    now_hour = datetime.now().hour
    congestion_factor = 1.0
    if 7 <= now_hour <= 9 or 17 <= now_hour <= 19:
        congestion_factor = 1.5
    
    # edge 길이에 혼잡 가중치 곱하기
    for u, v, data in G.edges(data=True):
        data['weight'] = data.get('length', 1) * congestion_factor
    
    return G

def find_optimal_route(G, start_point, end_point):
    orig_node = ox.nearest_nodes(G, start_point[1], start_point[0])
    dest_node = ox.nearest_nodes(G, end_point[1], end_point[0])
    
    try:
        route = nx.shortest_path(G, orig_node, dest_node, weight='weight')
        total_length = nx.shortest_path_length(G, orig_node, dest_node, weight='weight')
        # 속도 고려 (도보 5km/h, 자전거 15km/h, 차량 40km/h)
        return route, total_length
    except:
        return [], 0
