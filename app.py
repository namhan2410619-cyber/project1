import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from route import build_graph, find_optimal_route
from alarm import calculate_alarm_time
import osmnx as ox

st.set_page_config(page_title="스마트 통학 도우미", layout="wide")
st.title("🚍 현실 최적화 스마트 통학 알람 & 경로 지도")

# ----------------------
# 사용자 입력
# ----------------------
start = st.text_input("출발지", "서울역")
end = st.text_input("도착지", "고려대학교")
prep_time = st.number_input("준비 시간 (분)", min_value=0, value=30)
transport = st.selectbox("이동수단 선택", ["walk", "bike", "drive"])
school_hour = st.number_input("등교 시간 - 시", min_value=0, max_value=23, value=9)
school_minute = st.number_input("등교 시간 - 분", min_value=0, max_value=59, value=0)

if st.button("현실 최적화 경로 & 알람 계산"):

    # ----------------------
    # 좌표 변환
    # ----------------------
    geolocator = Nominatim(user_agent="commute_app")
    start_loc = geolocator.geocode(start)
    end_loc = geolocator.geocode(end)
    
    if not start_loc or not end_loc:
        st.error("주소를 찾을 수 없습니다.")
    else:
        start_point = (start_loc.latitude, start_loc.longitude)
        end_point = (end_loc.latitude, end_loc.longitude)

        # ----------------------
        # OSMnx 기반 그래프
        # ----------------------
        G = build_graph(start_point[0], start_point[1], transport)
        route_nodes, total_length = find_optimal_route(G, start_point, end_point)

        # 이동시간 계산 (속도 기반, 예시)
        speed_kmh = {"walk": 5, "bike": 15, "drive": 40}[transport]
        commute_time_min = total_length / 1000 / speed_kmh * 60

        # 스마트 알람
        alarm_time = calculate_alarm_time(prep_time, commute_time_min, school_hour, school_minute)

        st.success(f"총 이동 거리: {total_length/1000:.2f} km")
        st.info(f"추천 기상 시간: {alarm_time}")
        st.info(f"예상 이동 시간: {commute_time_min:.0f} 분")

        # ----------------------
        # 지도 표시
        # ----------------------
        m = folium.Map(location=[(start_point[0]+end_point[0])/2,
                                 (start_point[1]+end_point[1])/2], zoom_start=14)
        folium.Marker([start_point[0], start_point[1]], tooltip="출발지", popup=start, icon=folium.Icon(color="green")).add_to(m)
        folium.Marker([end_point[0], end_point[1]], tooltip="도착지", popup=end, icon=folium.Icon(color="red")).add_to(m)

        # Polyline 표시
        if route_nodes:
            route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route_nodes]
            folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.7).add_to(m)

        st_folium(m, width=900, height=600)

        # ----------------------
        # 실시간 교통 API 구조
        # ----------------------
        if transport in ["drive"]:  # 차량
            st.info("실시간 교통 혼잡 반영 가능 (예: Tmap/Google Maps Traffic API)")
        if transport in ["walk", "bike"]:
            st.info("도보/자전거는 평균 속도 기반")
