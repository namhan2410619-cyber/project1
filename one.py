# one.py  (single-file smart commute)
import streamlit as st
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
import requests
import math

# optional heavy libs will be imported lazily
try:
    import osmnx as ox
    import networkx as nx
    OSMNX_AVAILABLE = True
except Exception:
    OSMNX_AVAILABLE = False

# ---------------------------
# Config (여기에 실제 API 키 넣으세요)
# ---------------------------
BUS_API_KEY = "518211951a7b55f01e56382c9c1af89ccbcb85fe5b170e5af6acc01ed897aa3f"  # 경기도 예시
SUBWAY_API_KEY = "6763596c5a717a3033337a735a5559"  # 서울시 예시 (샘플)
# ---------------------------

st.set_page_config(page_title="스마트 통학 도우미", layout="wide")
st.title("스마트 통학 도우미 — 주소 기반 (single file)")

# ---------------------------
# Inputs (키워드 인수로 정확히)
# ---------------------------
start_addr = st.text_input("출발지 주소", "서울역")
end_addr   = st.text_input("도착지 주소", "고려대학교")
transport  = st.selectbox("이동수단", ["walk", "bike", "drive", "bus", "subway"])
prep_time  = st.number_input("준비시간 (분)", min_value=0, max_value=300, value=30, step=1)
breakfast  = st.number_input("아침(식사) 시간 (분)", min_value=0, max_value=120, value=20, step=1)
school_hour   = st.number_input("학교 도착 시각 (시)", min_value=0, max_value=23, value=9, step=1)
school_minute = st.number_input("학교 도착 시각 (분)", min_value=0, max_value=59, value=0, step=1)

# optional: for bus/subway actual query
col1, col2 = st.columns(2)
with col1:
    bus_route_id = st.text_input("버스 노선 ID (버스 선택 시 입력)", "")
with col2:
    station_id = st.text_input("정류장 ID (버스 선택 시 입력)", "")

subway_line = st.text_input("지하철 호선 (지하철 선택 시 입력, 예: 1)", "1")

# ---------------------------
# helper: haversine
# ---------------------------
def haversine_km(a, b):
    lat1, lon1 = a
    lat2, lon2 = b
    R = 6371.0
    phi1 = math.radians(lat1); phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1); dlambda = math.radians(lon2 - lon1)
    a_h = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a_h), math.sqrt(1 - a_h))
    return R * c

# ---------------------------
# Geocoding (Nominatim) with robust checks
# ---------------------------
geolocator = Nominatim(user_agent="smart_commute_singlefile")
try:
    start_loc = geolocator.geocode(start_addr, exactly_one=True, timeout=10)
    end_loc = geolocator.geocode(end_addr, exactly_one=True, timeout=10)
except Exception as e:
    st.error(f"지오코딩 실패: {e}")
    st.stop()

if not start_loc or not end_loc:
    st.error("출발지/도착지 주소를 찾을 수 없습니다. 주소를 더 정확히 입력해 주세요.")
    st.stop()

start_point = (start_loc.latitude, start_loc.longitude)
end_point = (end_loc.latitude, end_loc.longitude)

st.write(f"출발지 좌표: {start_point}, 도착지 좌표: {end_point}")

# ---------------------------
# compute travel time
# - If OSMnx available: compute real path length (meters)
# - Else fallback to haversine distance
# - For bus/subway: call API if keys + identifiers provided; otherwise fallback
# ---------------------------
def compute_distance_meters_osm(start_pt, end_pt, transport_mode):
    # returns length in meters or None on failure
    try:
        # choose network_type mapping
        net = {'walk':'walk','bike':'bike','drive':'drive'}.get(transport_mode, 'drive')
        # small radius centered at midpoint to avoid huge download
        mid_lat = (start_pt[0] + end_pt[0]) / 2
        mid_lon = (start_pt[1] + end_pt[1]) / 2
        # radius: make dynamic approximate by haversine*1.5 (meters), min 1000, max 5000
        approx_km = haversine_km(start_pt, end_pt)
        dist_m = max(1000, min(5000, int(approx_km * 1500)))  # heuristic
        G = ox.graph_from_point((mid_lat, mid_lon), dist=dist_m, network_type=net)
        orig = ox.nearest_nodes(G, start_pt[1], start_pt[0])
        dest = ox.nearest_nodes(G, end_pt[1], end_pt[0])
        length = nx.shortest_path_length(G, orig, dest, weight='length')
        return length
    except Exception as e:
        st.warning(f"OSM 경로 계산 실패: {e}")
        return None

def get_bus_eta_api(bus_route_id, station_id):
    if not BUS_API_KEY or not bus_route_id or not station_id:
        return None
    try:
        url = f"https://apis.data.go.kr/6410000/busarrivalservice/v2/arrivalsByRoute?serviceKey={BUS_API_KEY}&busRouteId={bus_route_id}&stationId={station_id}"
        r = requests.get(url, timeout=8)
        j = r.json()
        eta_list = j.get('response', {}).get('busArrivalList', [])
        if eta_list:
            # predictTime1 is minutes to arrival (경기도 예시)
            val = eta_list[0].get('predictTime1')
            if val is None:
                # fallback different key name
                val = eta_list[0].get('predictTime')
            return int(val) if val is not None else None
        return None
    except Exception as e:
        st.warning(f"버스 API 호출 실패: {e}")
        return None

def get_subway_eta_api(line_no, station_name=None):
    if not SUBWAY_API_KEY or not line_no:
        return None
    try:
        # We use realtimePosition endpoint example (XML). If user wants station-specific arrival, endpoint differs.
        url = f"http://swopenAPI.seoul.go.kr/api/subway/{SUBWAY_API_KEY}/xml/realtimePosition/0/10/{line_no}호선"
        r = requests.get(url, timeout=8)
        # parse XML to find nearest train ETA at station_name if provided
        # fallback: return None (because exact xml parsing requires known structure)
        return None
    except Exception as e:
        st.warning(f"지하철 API 호출 실패: {e}")
        return None

# compute base distance (meters)
distance_m = None
if OSMNX_AVAILABLE:
    # try OSMnx route-based length
    try:
        import networkx as nx
        distance_m = compute_distance_meters_osm(start_point, end_point, transport)
    except Exception as e:
        distance_m = None

if distance_m is None:
    # fallback to great-circle distance
    distance_km = haversine_km(start_point, end_point)
    distance_m = distance_km * 1000

# compute raw travel time (minutes) using realistic speeds (no arbitrary congest factors)
speeds = {"walk":5, "bike":15, "drive":40, "bus":30, "subway":35}  # km/h
speed_kmh = speeds.get(transport, 30)
travel_time_min = (distance_m/1000.0) / speed_kmh * 60.0

# If transport is bus/subway, try to add API-based waiting/delay
extra_wait_min = 0
if transport == "bus":
    api_eta = get_bus_eta_api(bus_route_id.strip(), station_id.strip())
    if api_eta is not None:
        extra_wait_min = api_eta
    else:
        # if API not available, show note and use a small default boarding wait
        extra_wait_min = 3
elif transport == "subway":
    api_eta = get_subway_eta_api(subway_line.strip(), None)
    if api_eta is not None:
        extra_wait_min = api_eta
    else:
        extra_wait_min = 2

total_commute_min = travel_time_min + extra_wait_min

# ---------------------------
# Smart alarm calculation
# ---------------------------
now = datetime.now()
school_time = now.replace(hour=int(school_hour), minute=int(school_minute), second=0, microsecond=0)
wake_time = school_time - timedelta(minutes=(prep_time + breakfast + total_commute_min))

# if wake_time is earlier than now, make it next day
if wake_time <= now:
    wake_time = wake_time + timedelta(days=1)

# ---------------------------
# Output
# ---------------------------
st.subheader("요약")
st.write(f"- 이동수단: **{transport}**")
st.write(f"- 출발지 좌표: {start_point}")
st.write(f"- 도착지 좌표: {end_point}")
st.write(f"- 거리(추정): **{round(distance_m/1000,3)} km**")
st.write(f"- 주행/이동 시간(추정): **{round(travel_time_min,1)} 분**")
st.write(f"- 버스/지하철 대기(추정/실제API 반영): **{round(extra_wait_min,1)} 분**")
st.write(f"- 총 소요 (대기 포함): **{round(total_commute_min,1)} 분**")
st.success(f"추천 기상 시각: **{wake_time.strftime('%Y-%m-%d %H:%M')}**")

# ---------------------------
# Map display
# ---------------------------
import folium
from streamlit_folium import st_folium

m = folium.Map(location=[(start_point[0]+end_point[0])/2, (start_point[1]+end_point[1])/2], zoom_start=14)
folium.Marker(location=start_point, tooltip="출발지", popup=start_addr).add_to(m)
folium.Marker(location=end_point, tooltip="도착지", popup=end_addr, icon=folium.Icon(color="red")).add_to(m)

# If osmnx route exists, attempt to draw polyline simplified
if OSMNX_AVAILABLE:
    try:
        mid_lat = (start_point[0] + end_point[0]) / 2
        approx_km = haversine_km(start_point, end_point)
        dist_m = max(1000, min(5000, int(approx_km * 1500)))
        G = ox.graph_from_point((mid_lat, (start_point[1]+end_point[1])/2), dist=dist_m, network_type={'walk':'walk','bike':'bike','drive':'drive'}.get(transport,'drive'))
        orig = ox.nearest_nodes(G, start_point[1], start_point[0])
        dest = ox.nearest_nodes(G, end_point[1], end_point[0])
        route_nodes = nx.shortest_path(G, orig, dest, weight='length')
        # sample nodes to keep polyline light
        route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for i,n in enumerate(route_nodes) if i%3==0]
        folium.PolyLine(route_coords, color="blue", weight=4, opacity=0.7).add_to(m)
    except Exception as e:
        st.info(f"경로 시각화 생략: {e}")

st_folium(m, width=800, height=600)

# ---------------------------
# Notes
# ---------------------------
st.subheader("설명 및 실행 팁")
st.write("- 실제 배차/지하철 API 키가 있으면 BUS_API_KEY/SUBWAY_API_KEY에 넣으세요.")
st.write("- OSMnx가 없으면 거리는 해버사인(직선) 기반으로 계산됩니다.")
st.write("- 개발환경에서 inotify(ENOSPC) 이슈 있으면 `streamlit run one.py --server.fileWatcherType=none` 로 실행하세요.")
