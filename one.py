# one.py — 주소 기반, 사용자 친화 UI, 자동 정류장/역 탐색(Overpass), 실시간 ETA 시도(가능하면), 스마트 기상 알람
# 한 파일로 동작합니다. 필요시 API 키에 실제 키를 넣으세요.
# 실행: streamlit run one.py --server.fileWatcherType=none

import streamlit as st
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
import requests
import math
import json
import time

# optional heavy libs used if available
try:
    import osmnx as ox
    import networkx as nx
    OSMNX = True
except Exception:
    OSMNX = False

# ==== CONFIG - 실제 키가 있으면 여기에 넣으세요 ====
BUS_API_KEY = "518211951a7b55f01e56382c9c1af89ccbcb85fe5b170e5af6acc01ed897aa3f"   # 경기도 예시
SUBWAY_API_KEY = "6763596c5a717a3033337a735a5559"  # 서울시 예시
# ===================================================

st.set_page_config(page_title="스마트 통학 도우미", layout="wide")
st.title("스마트 통학 도우미 — 주소 입력만으로 자동 계산")

# ===== Inputs =====
st.sidebar.header("설정")
start_addr = st.text_input("출발지 주소", "서울역")
end_addr = st.text_input("도착지 주소", "고려대학교")
transport = st.selectbox("이동수단", ["walk", "bike", "drive", "bus", "subway"])
prep_time = st.number_input("준비 시간 (분)", min_value=0, max_value=300, value=30, step=1)
breakfast_time = st.number_input("아침(식사) 시간 (분)", min_value=0, max_value=120, value=20, step=1)
school_hour = st.number_input("등교 시각 - 시", min_value=0, max_value=23, value=9, step=1)
school_minute = st.number_input("등교 시각 - 분", min_value=0, max_value=59, value=0, step=1)
search_radius_m = st.slider("정류장/역 자동탐색 반경 (m)", min_value=200, max_value=3000, value=1000, step=100)

if st.button("계산 시작"):
    # ===== geocode addresses =====
    geolocator = Nominatim(user_agent="smart_commute_app")
    try:
        start_geo = geolocator.geocode(start_addr, timeout=10)
        end_geo = geolocator.geocode(end_addr, timeout=10)
    except Exception as e:
        st.error(f"주소 변환 실패: {e}")
        st.stop()

    if not start_geo or not end_geo:
        st.error("출발지 또는 도착지를 찾을 수 없습니다. 주소를 더 정확히 입력하세요.")
        st.stop()

    start_pt = (start_geo.latitude, start_geo.longitude)
    end_pt = (end_geo.latitude, end_geo.longitude)
    st.subheader("입력 확인")
    st.write(f"출발지: {start_addr} → {start_pt}")
    st.write(f"도착지: {end_addr} → {end_pt}")

    # ===== helper functions =====
    def haversine_km(a, b):
        lat1, lon1 = a; lat2, lon2 = b
        R = 6371.0
        phi1 = math.radians(lat1); phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1); dlambda = math.radians(lon2 - lon1)
        a_ = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a_), math.sqrt(1 - a_))
        return R * c

    def overpass_nearby(lat, lon, radius, tags):
        # tags: list of OSM filters, e.g. ['"highway"="bus_stop"']
        q_filters = "".join([f"node[{t}](around:{radius},{lat},{lon});" for t in tags])
        query = f"[out:json][timeout:25];({q_filters});out body;>;out skel qt;"
        url = "https://overpass-api.de/api/interpreter"
        try:
            r = requests.post(url, data={"data": query}, timeout=20)
            data = r.json()
            nodes = []
            for el in data.get("elements", []):
                if el.get("type") == "node" and "tags" in el:
                    nodes.append(el)
            return nodes
        except Exception:
            return []

    # ===== find nearby stops/stations automatically =====
    st.subheader("주변 정류장/역 자동 탐색")
    if transport in ("bus",):
        tags = ['"highway"="bus_stop"', '"public_transport"="platform"']
        nodes = overpass_nearby(start_pt[0], start_pt[1], search_radius_m, tags)
        if not nodes:
            st.info("근처 OSM 버스 정류장을 찾지 못했습니다. 반경을 늘리거나 주소를 확인하세요.")
            nearest_bus = None
        else:
            # choose nearest by distance
            nodes_sorted = sorted(nodes, key=lambda n: haversine_km((n['lat'], n['lon']), start_pt))
            nearest = nodes_sorted[0]
            nearest_bus = {"name": nearest.get("tags", {}).get("name", "무명 정류장"),
                           "lat": nearest["lat"], "lon": nearest["lon"]}
            st.write(f"자동 선택된 정류장: {nearest_bus['name']} ({nearest_bus['lat']:.6f}, {nearest_bus['lon']:.6f})")
    else:
        nearest_bus = None

    if transport in ("subway",):
        tags = ['"railway"="station"', '"station"="subway"']
        nodes = overpass_nearby(start_pt[0], start_pt[1], search_radius_m, tags)
        if not nodes:
            # Try any railway station
            nodes = overpass_nearby(start_pt[0], start_pt[1], search_radius_m, ['"railway"="station"'])
        if not nodes:
            st.info("근처 지하철 역을 찾지 못했습니다. 반경을 늘리거나 주소를 확인하세요.")
            nearest_station = None
        else:
            nodes_sorted = sorted(nodes, key=lambda n: haversine_km((n['lat'], n['lon']), start_pt))
            nearest = nodes_sorted[0]
            nearest_station = {"name": nearest.get("tags", {}).get("name", "무명 역"),
                               "lat": nearest["lat"], "lon": nearest["lon"]}
            st.write(f"자동 선택된 역: {nearest_station['name']} ({nearest_station['lat']:.6f}, {nearest_station['lon']:.6f})")
    else:
        nearest_station = None

    # ===== compute distance and base travel time (no arbitrary congestion) =====
    if OSMNX:
        try:
            mid_lat = (start_pt[0] + end_pt[0]) / 2
            mid_lon = (start_pt[1] + end_pt[1]) / 2
            approx_km = haversine_km(start_pt, end_pt)
            radius = min(max(1000, int(approx_km * 1500)), 5000)
            network_type = {'walk':'walk','bike':'bike','drive':'drive'}.get(transport, 'drive')
            G = ox.graph_from_point((mid_lat, mid_lon), dist=radius, network_type=network_type)
            orig = ox.nearest_nodes(G, start_pt[1], start_pt[0])
            dest = ox.nearest_nodes(G, end_pt[1], end_pt[0])
            length_m = nx.shortest_path_length(G, orig, dest, weight='length')
        except Exception as e:
            st.warning(f"OSM 경로 계산 실패, 직선거리로 대체합니다: {e}")
            length_m = haversine_km(start_pt, end_pt) * 1000.0
    else:
        length_m = haversine_km(start_pt, end_pt) * 1000.0

    speeds = {"walk":5, "bike":15, "drive":40, "bus":30, "subway":35}  # km/h typical
    base_travel_min = (length_m/1000.0) / speeds.get(transport,30) * 60.0

    # ===== attempt to get real-time waiting ETA for bus/subway; if API fails, fallback to small default wait =====
    wait_min = 0.0
    note_lines = []
    if transport == "bus" and nearest_bus:
        # Try to find station id via gov API (best-effort); if not found, fallback.
        # We attempt to call a generic station-search endpoint (may vary by provider); if fails, skip.
        try:
            # OVERPASS gave us name; try to query 경기도 API station list by name (best-effort endpoint guess)
            station_name = nearest_bus["name"]
            # There is no universal station search endpoint format guaranteed here; try one plausible endpoint and fall back.
            # If this fails, we simply estimate boarding wait of 3-6 minutes.
            # Attempt: call a hypothetical station list endpoint (this may fail depending on provider).
            url_search = f"https://apis.data.go.kr/6410000/busstationservice/getBusStationList?serviceKey={BUS_API_KEY}&keyword={requests.utils.quote(station_name)}"
            r = requests.get(url_search, timeout=6)
            if r.status_code == 200:
                try:
                    j = r.json()
                    # try to parse common json structure
                    stations = j.get('response', {}).get('body', {}).get('items', [])
                    if not stations:
                        stations = j.get('response', {}).get('busStationList', []) or []
                except Exception:
                    stations = []
            else:
                stations = []
            if stations:
                # pick first, try to obtain stationId and call arrivalsByRoute-like endpoint
                st_id = None
                # Different providers use different keys; try multiple common keys
                item0 = stations[0]
                st_id = item0.get("stationId") or item0.get("arsId") or item0.get("stationid") or item0.get("station_id")
                if st_id:
                    url_arr = f"https://apis.data.go.kr/6410000/busarrivalservice/v2/arrivalsByStation?serviceKey={BUS_API_KEY}&stationId={st_id}"
                    r2 = requests.get(url_arr, timeout=6)
                    if r2.status_code == 200:
                        try:
                            j2 = r2.json()
                            arrs = j2.get('response', {}).get('busArrivalList', []) or j2.get('response', {}).get('body', {}).get('items', [])
                            if arrs:
                                # take earliest predictTime (minutes)
                                mins = []
                                for it in arrs:
                                    v = it.get('predictTime1') or it.get('predictTime') or it.get('remainMin')
                                    if v is None:
                                        continue
                                    try:
                                        mins.append(int(v))
                                    except:
                                        pass
                                if mins:
                                    wait_min = float(min(mins))
                                    note_lines.append(f"실시간 버스 대기 반영 ({int(wait_min)}분)")
                                else:
                                    wait_min = 3.0
                                    note_lines.append("버스 도착시간 파싱 불가 — 기본 대기 3분 적용")
                            else:
                                wait_min = 3.0
                                note_lines.append("버스 도착 데이터 없음 — 기본 대기 3분 적용")
                        except Exception:
                            wait_min = 3.0
                            note_lines.append("버스 도착 파싱 실패 — 기본 대기 3분 적용")
                    else:
                        wait_min = 3.0
                        note_lines.append("버스 API 호출 실패 — 기본 대기 3분 적용")
                else:
                    wait_min = 3.0
                    note_lines.append("정류장 ID 없음 — 기본 대기 3분 적용")
            else:
                wait_min = 3.0
                note_lines.append("정류장 검색 실패 — 기본 대기 3분 적용")
        except Exception as e:
            wait_min = 3.0
            note_lines.append(f"버스 ETA 처리 에러: {e} — 기본 대기 3분 적용")
    elif transport == "subway" and nearest_station:
        try:
            station_name = nearest_station["name"]
            # Seoul API example expects station name; we'll call realtimeStationArrival endpoint
            url = f"http://swopenAPI.seoul.go.kr/api/subway/{SUBWAY_API_KEY}/json/realtimeStationArrival/0/5/{requests.utils.quote(station_name)}"
            r = requests.get(url, timeout=6)
            if r.status_code == 200:
                j = r.json()
                arrs = j.get("realtimeArrivalList") or j.get("realtimeArrivalList", [])
                if arrs:
                    # barvlDt is remaining time in seconds sometimes, or barvlTp etc. We'll try common fields
                    mins = []
                    for it in arrs:
                        # barvlDt may be seconds to arrival
                        sec = it.get("barvlDt") or it.get("barvldt")
                        if sec:
                            try:
                                mins.append(int(sec)/60.0)
                            except:
                                pass
                        # arvlMsg2 may contain like '전역 도착' etc - skip
                    if mins:
                        wait_min = float(min(mins))
                        note_lines.append(f"실시간 열차 대기 반영 ({int(wait_min)}분)")
                    else:
                        wait_min = 2.0
                        note_lines.append("지하철 도착 파싱 불가 — 기본 대기 2분 적용")
                else:
                    wait_min = 2.0
                    note_lines.append("지하철 도착 데이터 없음 — 기본 대기 2분 적용")
            else:
                wait_min = 2.0
                note_lines.append("지하철 API 호출 실패 — 기본 대기 2분 적용")
        except Exception as e:
            wait_min = 2.0
            note_lines.append(f"지하철 ETA 처리 에러: {e} — 기본 대기 2분 적용")
    else:
        # for walk/bike/drive default no extra wait
        wait_min = 0.0

    total_min = base_travel_min + wait_min
    # compute wake time
    now = datetime.now()
    school_dt = now.replace(hour=int(school_hour), minute=int(school_minute), second=0, microsecond=0)
    wake_dt = school_dt - timedelta(minutes=(prep_time + breakfast_time + total_min))
    if wake_dt <= now:
        wake_dt += timedelta(days=1)

    # ===== output =====
    st.subheader("예상 결과")
    st.write(f"- 추정 거리: **{round(length_m/1000,3)} km**")
    st.write(f"- 주행/이동 시간(추정): **{round(base_travel_min,1)} 분**")
    st.write(f"- 대기/탑승 시간(추정): **{round(wait_min,1)} 분**")
    st.write(f"- 총 소요 시간 (대기 포함): **{round(total_min,1)} 분**")
    st.success(f"권장 기상 시각: **{wake_dt.strftime('%Y-%m-%d %H:%M')}**")

    if note_lines:
        for ln in note_lines:
            st.info(ln)

    # ===== Map visualization =====
    import folium
    from streamlit_folium import st_folium
    m = folium.Map(location=[(start_pt[0]+end_pt[0])/2, (start_pt[1]+end_pt[1])/2], zoom_start=14)
    folium.Marker(location=start_pt, popup="출발지", tooltip=start_addr, icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(location=end_pt, popup="도착지", tooltip=end_addr, icon=folium.Icon(color="red")).add_to(m)
    if transport in ("bus",) and nearest_bus:
        folium.CircleMarker(location=(nearest_bus['lat'], nearest_bus['lon']), radius=6, color="orange", fill=True, popup=nearest_bus['name']).add_to(m)
    if transport in ("subway",) and nearest_station:
        folium.CircleMarker(location=(nearest_station['lat'], nearest_station['lon']), radius=6, color="purple", fill=True, popup=nearest_station['name']).add_to(m)

    # attempt to draw route using OSMnx if available
    if OSMNX:
        try:
            mid_lat = (start_pt[0]+end_pt[0])/2
            approx_km = haversine_km(start_pt, end_pt)
            radius = max(1000, min(5000, int(approx_km*1500)))
            Gv = ox.graph_from_point((mid_lat, (start_pt[1]+end_pt[1])/2), dist=radius, network_type={'walk':'walk','bike':'bike','drive':'drive'}.get(transport,'drive'))
            origv = ox.nearest_nodes(Gv, start_pt[1], start_pt[0])
            destv = ox.nearest_nodes(Gv, end_pt[1], end_pt[0])
            routev = nx.shortest_path(Gv, origv, destv, weight='length')
            route_coords = [(Gv.nodes[n]['y'], Gv.nodes[n]['x']) for i,n in enumerate(routev) if i%3==0]
            folium.PolyLine(route_coords, color="blue", weight=4, opacity=0.7).add_to(m)
        except Exception as e:
            st.info(f"경로 시각화에서 OSMnx 오류: {e}")

    st.subheader("지도")
    st_folium(m, width=900, height=600)
