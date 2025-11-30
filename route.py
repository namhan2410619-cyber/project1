import networkx as nx

def build_graph(transport):

    G = nx.Graph()

    # 샘플 노드 (실서비스: API로 갱신)
    G.add_weighted_edges_from([
        ("출발", "환승센터", 10),
        ("환승센터", "도착", 15)
    ])

    # 이동수단 가중치 정책
    if transport == "도보":
        speed_factor = 1.2
    elif transport == "버스":
        speed_factor = 0.8
    elif transport == "지하철":
        speed_factor = 0.6
    else:
        speed_factor = 1.0

    for u, v, data in G.edges(data=True):
        data['weight'] *= speed_factor

    return G
