import networkx as nx

def build_graph(transport):
    G = nx.Graph()

    # 샘플 노드, 실제 API 연동 시 여기서 실시간 교통 반영
    G.add_weighted_edges_from([
        ("출발", "중간지점", 8),
        ("중간지점", "도착", 12)
    ])

    speed_factor = {
        "도보": 1.2,
        "버스": 0.8,
        "지하철": 0.6,
        "자전거": 1.0
    }.get(transport, 1.0)

    for u, v, data in G.edges(data=True):
        data["weight"] *= speed_factor

    return G

def find_optimal_route(graph, start, end):
    try:
        route = nx.shortest_path(graph, start, end, weight="weight")
        total_time = nx.shortest_path_length(graph, start, end, weight="weight")
        return route, total_time
    except:
        return ["경로 없음"], 999
