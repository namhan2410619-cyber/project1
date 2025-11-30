import networkx as nx

def build_graph(transport):
    G = nx.Graph()

    # 샘플 데이터 - 실제 서비스: API 기반 자동 구성
    G.add_weighted_edges_from([
        ("출발", "중간지점", 8),
        ("중간지점", "도착", 12)
    ])

    speed = {
        "도보": 1.2,
        "버스": 0.8,
        "지하철": 0.6,
        "자전거": 1.0
    }.get(transport, 1.0)

    for u, v, data in G.edges(data=True):
        data["weight"] *= speed

    return G


def find_optimal_route(graph, start, end):
    try:
        route = nx.shortest_path(graph, start, end, weight="weight")
        time = nx.shortest_path_length(graph, start, end, weight="weight")
        return route, time
    except:
        return ["경로 없음"], 999
