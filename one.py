
import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="스마트 통학 도우미", layout="wide", page_icon="🚀")
st.title("스마트 통학 도우미 - 실시간 교통 기반")

# --------------------------
# 사용자 입력
# --------------------------
start_addr = st.text_input("출발지 주소", "서울시 종로구 청와대로 1")
end_addr   = st.text_input("도착지 주소", "서울시 종로구 세종대로 110")
transport  = st.selectbox("이동수단", ["walk", "bike", "drive", "bus", "subway"])
prep_time  = st.number_input("준비시간(분)", 30, step=5)
breakfast  = st.number_input("아침시간(분)", 20, step=5)
school_hour   = st.number_input("학교 도착 시각(시)", 9, 0, 23)
school_minute = st.number_input("학교 도착 시각(분)", 0, 0, 59)

# --------------------------
# 주소 → 좌표 변환
# --------------------------
geolocator = Nominatim(user_agent="smart_commute")
try:
    start_loc = geolocator.geocode(start_addr)
    end_loc   = geolocator.geocode(end_addr)
    start_point = (start_loc.latitude, start_loc.longitude)
    end_point   = (end_loc.latitude, end_loc.longitude)
except:
    st.error("주소 변환 실패")
    st.stop()

# --------------------------
# 예상 이동 시간 계산 (실제 API 기반)
# --------------------------
def get_bus_time(start, end):
    # 예시: 경기도 버스 도착정보 API 호출
    # 실제 API key, 정류소 ID 필요
    api_key = "6763596c5a717a3033337a735a5559"
    # 여기서는 더미 값
    return 20  # 분 단위

def get_subway_time(start, end):
    # 예시: 서울 지하철 실시간 열차위치 API
    # 실제 API key 필요
    api_key = "YOUR_SEOUL_SUBWAY_API_KEY"
    # 더미 값
    return 15  # 분 단위

def get_drive_time(start, end):
    # 단순 거리/속도 계산
    import osmnx as ox
    import networkx as nx
    G = ox.graph_from_point(start, dist=3000, network_type='drive')
    orig = ox.nearest_nodes(G, start[1], start[0])
    dest = ox.nearest_nodes(G, end[1], end[0])
    try:
        length = nx.shortest_path_length(G, orig, dest, weight='length')
        speed_kmh = 40
        return length/1000/speed_kmh*60
    except:
        return 30

def get_walk_time(start, end):
    import osmnx as ox
    import networkx as nx
    G = ox.graph_from_point(start, dist=2000, network_type='walk')
    orig = ox.nearest_nodes(G, start[1], start[0])
    dest = ox.nearest_nodes(G, end[1], end[0])
    try:
        length = nx.shortest_path_length(G, orig, dest, weight='length')
        speed_kmh = 5
        return length/1000/speed_kmh*60
    except:
        return 15

def get_bike_time(start, end):
    import osmnx as ox
    import networkx as nx
    G = ox.graph_from_point(start, dist=2500, network_type='bike')
    orig = ox.nearest_nodes(G, start[1], start[0])
    dest = ox.nearest_nodes(G, end[1], end[0])
    try:
        length = nx.shortest_path_length(G, orig, dest, weight='length')
        speed_kmh = 15
        return length/1000/speed_kmh*60
    except:
        return 15

commute_time = 0
if transport=="bus":
    commute_time = get_bus_time(start_point, end_point)
elif transport=="subway":
    commute_time = get_subway_time(start_point, end_point)
elif transport=="drive":
    commute_time = get_drive_time(start_point, end_point)
elif transport=="walk":
    commute_time = get_walk_time(start_point, end_point)
elif transport=="bike":
    commute_time = get_bike_time(start_point, end_point)

# --------------------------
# 스마트 알람 계산
# --------------------------
school_time = datetime.combine(datetime.today(), datetime.min.time()).replace(hour=int(school_hour), minute=int(school_minute))
wake_time = school_time - timedelta(minutes=(prep_time + breakfast + commute_time))
st.info(f"추천 알람 시간: {wake_time.strftime('%H:%M')} (준비시간 포함)")

# --------------------------
# 지도 표시
# --------------------------
import folium
from streamlit_folium import st_folium

m = folium.Map(location=start_point, zoom_start=14)
folium.Marker(start_point, tooltip="출발지").add_to(m)
folium.Marker(end_point, tooltip="도착지", icon=folium.Icon(color="red")).add_to(m)
st.subheader("예상 경로 지도")
st.write(f"예상 이동시간: {round(commute_time,1)} 분")
st_folium(m, width=700, height=500)

# --------------------------
# 실시간 API 안내
# --------------------------
st.subheader("실시간 교통 API 안내")
st.write("실제 배차/지하철 열차 위치 API를 연동하면 더 정확한 예상시간 계산 가능")
st.write("버스: 경기도 버스 도착정보 API, 지하철: 서울시 지하철 실시간 API")
