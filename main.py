# streamlit_app.py
"""
Smart Commute Alarm - Streamlit Prototype (실무 실행용)
Features:
 - Graph (nodes/edges) with time-dependent edge weights
 - Dijkstra variant for time-dependent weights
 - PriorityQueue (heap) usage to sort upcoming departures
 - Simulated real-time delays and optional API hook points
 - Outputs recommended wake time and leave time
Notes:
 - Replace placeholder API key strings and API-call functions with real implementations
 - This prototype is intentionally self-contained for offline testing
"""

import streamlit as st
import heapq
import datetime
import math
import random
import time
from typing import Dict, List, Callable, Tuple, Optional

st.set_page_config(page_title="Smart Commute Alarm - Ready-to-run", layout="wide")

# -------------------------
# ----- Utility helpers ----
# -------------------------
def now_local():
    return datetime.datetime.now()

def minutes_to_td(m: int):
    return datetime.timedelta(minutes=m)

def format_dt(dt: datetime.datetime):
    return dt.strftime("%Y-%m-%d %H:%M")

# -------------------------
# ----- Data structures ----
# -------------------------
class Edge:
    def __init__(self, to_node: str, base_min: int,
                 delay_fn: Optional[Callable[[datetime.datetime, int], int]] = None,
                 meta: dict = None):
        """
        to_node: destination node id
        base_min: base travel time in minutes (static)
        delay_fn: function(current_time: datetime, elapsed_min:int) -> extra_delay_minutes (int)
        meta: optional metadata (e.g., stop_id, transport_type)
        """
        self.to_node = to_node
        self.base_min = base_min
        self.delay_fn = delay_fn
        self.meta = meta or {}

    def effective_time(self, current_time: datetime.datetime, elapsed_min:int) -> int:
        """Return base + realtime delay (in minutes)."""
        delay = 0
        if self.delay_fn:
            try:
                d = self.delay_fn(current_time, elapsed_min)
                if isinstance(d, (int, float)):
                    delay = int(d)
            except Exception as e:
                # fail-safe: no extra delay
                delay = 0
        return int(self.base_min + delay)

class Graph:
    def __init__(self):
        self.adj: Dict[str, List[Edge]] = {}

    def add_node(self, node_id: str):
        if node_id not in self.adj:
            self.adj[node_id] = []

    def add_edge(self, from_node: str, to_node: str, base_min: int,
                 delay_fn: Optional[Callable[[datetime.datetime, int], int]] = None,
                 meta: dict = None):
        self.add_node(from_node)
        self.add_node(to_node)
        self.adj[from_node].append(Edge(to_node, base_min, delay_fn, meta))

    def neighbors(self, node_id: str) -> List[Edge]:
        return self.adj.get(node_id, [])

# -------------------------
# ----- Time-dependent Dijkstra ----
# -------------------------
def dijkstra_time_dependent(graph: Graph, start: str, goal: str, depart_time: datetime.datetime) -> Tuple[float, List[str]]:
    """
    Returns (travel_time_minutes, path_nodes)
    The algorithm tracks elapsed minutes from depart_time and uses edge.effective_time(depart_time, elapsed).
    This is a label-setting Dijkstra using elapsed time as cost.
    """
    INF = float("inf")
    dist = {node: INF for node in graph.adj.keys()}
    prev = {}
    # priority queue of (elapsed_minutes, node)
    pq = []
    dist[start] = 0
    heapq.heappush(pq, (0, start))

    while pq:
        elapsed_min, node = heapq.heappop(pq)
        if elapsed_min > dist[node]:
            continue
        if node == goal:
            break
        for edge in graph.neighbors(node):
            # compute effective edge travel time given current elapsed
            eff = edge.effective_time(depart_time, elapsed_min)
            new_cost = elapsed_min + eff
            if new_cost < dist.get(edge.to_node, INF):
                dist[edge.to_node] = new_cost
                prev[edge.to_node] = node
                heapq.heappush(pq, (new_cost, edge.to_node))

    if dist.get(goal, INF) == INF:
        return INF, []
    # reconstruct path
    path = []
    cur = goal
    while cur != start:
        path.append(cur)
        cur = prev.get(cur, start)
        if cur is None:
            break
    path.append(start)
    path.reverse()
    return dist[goal], path

# -------------------------
# ----- Simulated / API delay providers ----
# -------------------------
def simulated_random_delay_provider(max_delay_min: int, seed=None):
    rnd = random.Random(seed)
    def fn(current_time: datetime.datetime, elapsed_min:int):
        # slight deterministic variability based on minute-of-day
        base = rnd.randint(0, max_delay_min)
        # simulate peak-hour multiplier
        hour = current_time.hour
        peak_multiplier = 1
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            peak_multiplier = 1.5
        return int(base * peak_multiplier)
    return fn

# Placeholder for a real bus API call (implementer: replace body with real requests)
def seoul_bus_arrival_delay_stub(stop_id: str):
    """
    Return function(current_time, elapsed_min) -> delay_minutes
    Replace body with actual API parsing. For now we return a lambda that simulates small delays.
    """
    def fn(current_time: datetime.datetime, elapsed_min:int):
        # Example: if stop_id ends with digit, make deterministic small delay
        try:
            d = int(str(stop_id)[-1]) % 3
        except Exception:
            d = 0
        # small random jitter
        jitter = random.randint(0,2)
        # peak hours more likely to have delay
        if 7 <= current_time.hour <= 9:
            d += 1
        return d + jitter
    return fn

# -------------------------
# ----- Heap (priority queue) example: upcoming departures sorted ----
# -------------------------
def top_k_departures(departure_list: List[Tuple[int, str]], k: int):
    """
    departure_list: list of (minutes_until_departure, "Bus 123 at Stop A")
    Return top-k soonest departures using heap (min-heap).
    """
    pq = departure_list[:]
    heapq.heapify(pq)
    topk = []
    for _ in range(min(k, len(pq))):
        topk.append(heapq.heappop(pq))
    return topk

# -------------------------
# ----- Streamlit UI ----
# -------------------------
st.title("Smart Commute Alarm — 실무용 프로토타입")
st.markdown("이 앱은 **그래프 기반 최단 경로 (시간 의존)** + **스마트 기상 알람 계산** + **우선순위 큐(배차 정렬)** 예시를 포함합니다.")

with st.sidebar:
    st.header("기본 설정")
    home = st.text_input("Home (node id 또는 'lat,lon' 표기 가능)", value="Home")
    destination = st.text_input("Destination (node id)", value="School")
    commute_mode = st.selectbox("Primary mode", ["transit", "bicycle", "walking", "driving"])
    desired_arrival_time = st.time_input("Desired arrival time at destination", value=datetime.time(hour=8, minute=30))
    buffer_before = st.number_input("Buffer before class (minutes)", 0, 120, 5)
    prep_shower = st.number_input("Shower time (minutes)", 0, 60, 10)
    prep_breakfast = st.number_input("Breakfast time (minutes)", 0, 60, 15)
    prep_other = st.number_input("Other prep time (minutes)", 0, 60, 10)
    st.markdown("---")
    st.subheader("Graph / Edge options")
    use_sample_graph = st.checkbox("Use sample demo graph (recommended)", value=True)
    simulate_max_delay = st.slider("Simulate max extra delay per edge (minutes)", 0, 20, 5)
    st.markdown("---")
    st.subheader("API Keys & Hooks (옵션)")
    google_key = st.text_input("Google Directions API key (optional)", value="", help="실제 길찾이 연동 시 사용")
    seoul_bus_key = st.text_input("Seoul Bus API key (optional)", value="", help="서울시 버스 실시간 도착")

col1, col2 = st.columns([2,1])

with col1:
    st.subheader("Graph 구성 / 편집")
    if use_sample_graph:
        st.markdown("샘플 그래프 사용: Home → StopA → Transfer → Station → School (버스+도보+지하철 혼합)")
        g = Graph()
        # Home -> StopA (walk 5)
        g.add_edge("Home", "StopA", base_min=5, delay_fn=None, meta={"type":"walk"})
        # StopA -> StopB (bus ride 15) - use simulated bus delay provider
        g.add_edge("StopA", "StopB", base_min=15, delay_fn=simulated_random_delay_provider(simulate_max_delay), meta={"type":"bus", "stop_id":"S1"})
        # StopB -> Transfer (walk 3)
        g.add_edge("StopB", "Transfer", base_min=3, delay_fn=None, meta={"type":"walk"})
        # Transfer -> Station (bus 8)
        g.add_edge("Transfer", "Station", base_min=8, delay_fn=simulated_random_delay_provider(simulate_max_delay), meta={"type":"bus", "stop_id":"S2"})
        # Station -> School (subway 10)
        g.add_edge("Station", "School", base_min=10, delay_fn=simulated_random_delay_provider(max(2, simulate_max_delay//2)), meta={"type":"subway", "station_id":"ST1"})
        # add alternate walking-only route directly (long)
        g.add_edge("Home", "School", base_min=45, delay_fn=None, meta={"type":"walking"})
    else:
        st.markdown("직접 그래프를 구성하려면 '직접 편집' 체크 후 노드/간선 추가 기능을 구현하세요.")
        st.stop()

    st.markdown("**그래프 요약(노드별 연결)**")
    for node, edges in g.adj.items():
        st.write(f"- {node}:")
        for e in edges:
            st.write(f"    -> {e.to_node} | base {e.base_min} min | type={e.meta.get('type')}")

with col2:
    st.subheader("실행 제어")
    # compute times when button pressed
    if st.button("Compute recommended wake & leave times"):
        # compute arrival datetime (today or next day logic)
        today = datetime.date.today()
        arrival_dt = datetime.datetime.combine(today, desired_arrival_time)
        if arrival_dt < now_local():
            arrival_dt += datetime.timedelta(days=1)
        st.write(f"Desired arrival: **{format_dt(arrival_dt)}**")

        # We want to find travel time from Home to Destination when leaving at some time.
        # We'll compute travel time assuming we leave at various candidate leave times,
        # but standard approach: run dijkstra assuming depart_time = leave_time to get travel duration.
        # Instead we find leave_time = arrival - travel_minutes - buffer
        # But travel_minutes depends on leave_time. Solve iteratively:
        leave_guess = arrival_dt - datetime.timedelta(minutes=30)  # initial guess (30 min before)
        # iterate to convergence
        max_iter = 6
        tol_min = 1  # stop when leave time changes < tol_min
        last_leave = None
        for i in range(max_iter):
            travel_min, path = dijkstra_time_dependent(g, start=home, goal=destination, depart_time=leave_guess)
            if math.isinf(travel_min):
                st.error("경로를 찾을 수 없습니다. 그래프를 확인하세요.")
                travel_min = 9999
                path = []
                break
            recommended_leave = arrival_dt - datetime.timedelta(minutes=(int(travel_min) + int(buffer_before)))
            # if change small, break
            if last_leave:
                diff = abs((recommended_leave - last_leave).total_seconds() / 60.0)
                if diff < tol_min:
                    last_leave = recommended_leave
                    break
            last_leave = recommended_leave
            # next iteration: set leave_guess to recommended_leave (we're solving fixed point)
            leave_guess = recommended_leave

        # compute wake time
        total_prep = int(prep_shower) + int(prep_breakfast) + int(prep_other)
        wake_dt = last_leave - datetime.timedelta(minutes=total_prep)

        st.success(f"Recommended LEAVE time: **{format_dt(last_leave)}**")
        st.success(f"Recommended WAKE (alarm): **{format_dt(wake_dt)}**")
        st.write(f"Estimated travel time (minutes): **{int(travel_min)}**")
        st.write("Chosen path:", " → ".join(path))

        # timeline
        timeline = {
            "Now": format_dt(now_local()),
            "Wake (alarm)": format_dt(wake_dt),
            "Prep finished": format_dt(wake_dt + datetime.timedelta(minutes=total_prep)),
            "Leave": format_dt(last_leave),
            "Arrive (target)": format_dt(arrival_dt)
        }
        st.markdown("**Timeline**")
        for k, v in timeline.items():
            st.write(f"- {k}: {v}")

        # Show per-edge breakdown with effective times
        st.markdown("**Path edge breakdown (effective minutes per edge at departure time)**")
        elapsed = 0
        for i in range(len(path)-1):
            from_node = path[i]
            to_node = path[i+1]
            # find matching edge
            edges = [e for e in g.neighbors(from_node) if e.to_node == to_node]
            if not edges:
                continue
            e = edges[0]
            eff = e.effective_time(last_leave, elapsed)
            st.write(f"- {from_node} -> {to_node} | base {e.base_min} min | effective {eff} min | type={e.meta.get('type')}")
            elapsed += eff

        # demonstrate priority queue of upcoming departures (simulated)
        st.markdown("**Upcoming departures (simulated) — heap sort demo**")
        simulated_departures = []
        # create some sample departures (minutes until depart, description)
        for i in range(6):
            minutes_until = random.randint(1, 30)
            desc = f"Bus {100+i} at StopX in {minutes_until} min"
            simulated_departures.append((minutes_until, desc))
        top3 = top_k_departures(simulated_departures, 3)
        st.write("Soonest 3 departures (minutes, desc):")
        for m, d in top3:
            st.write(f"- {m} min — {d}")

        # Provide suggestion rules
        st.markdown("**Smart rules**")
        # simple heuristics: if any edge effective > base+threshold -> advance wake
        adv_minutes = 0
        for from_node in g.adj:
            for e in g.adj[from_node]:
                # if bus/subway and large extra delay
                base = e.base_min
                eff = e.effective_time(last_leave, 0)
                if e.meta.get("type") in ("bus", "subway") and eff - base >= max(5, simulate_max_delay//2):
                    adv_minutes = max(adv_minutes, eff - base)
        if adv_minutes > 0:
            st.warning(f"지연 감지(예상). 권장: WAKE를 {adv_minutes}분 앞당기세요.")
        else:
            st.info("현재 시뮬레이션 기준으로 큰 지연 없음.")

st.markdown("---")
st.caption("참고: 실제 연결 시 아래 작업을 하세요: (1) Geocoding으로 주소->좌표 → 그래프 자동 생성 (2) Google Directions / OpenRouteService로 실제 edge base 값을 채우기 (3) 공공데이터/버스 API로 delay_fn을 구현하여 edge 중 실시간 데이터 반영 (4) 모바일 앱 / FCM으로 실제 알람 전송")
