import streamlit as st
import folium
from streamlit_folium import st_folium
from route import build_graph, find_optimal_route

st.set_page_config(page_title="스마트 통학 도우미", layout="wide", page_icon="🚀")

st.title("스마트 통학 도우미")

# 입력
col1, col2 = st.columns(2)
with col1:
    start_lat = st.number_input("출발지 위도", value=37.5665)
    start_lon = st.number_input("출발지 경도", value=126.9780)
with col2:
    end_lat = st.number_input("도착지 위도", value=37.5700)
    end_lon = st.number_input("도착지 경도", value=126.9920)

transport = st.selectbox("이동수단", ["walk", "bike", "drive", "bus"])

if st.button("최적 경로 계산"):
    G = build_graph(start_lat, start_lon, transport)
    route_nodes, total_length = find_optimal_route(G, (start_lat, start_lon), (end_lat, end_lon))

    if not route_nodes:
        st.error("경로 계산 실패")
    else:
        # Polyline 샘플링: 3개 단위
        route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for i, n in enumerate(route_nodes) if i % 3 == 0]

        # 지도 표시
        m = folium.Map(location=[start_lat, start_lon], zoom_start=14)
        folium.Marker([start_lat, start_lon], tooltip="출발지").add_to(m)
        folium.Marker([end_lat, end_lon], tooltip="도착지", icon=folium.Icon(color="red")).add_to(m)
        folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.7).add_to(m)

        st_folium(m, width=700, height=500)

        # 예상 시간 계산 (속도 단위 km/h)
        speed_kmh = {"walk":5, "bike":15, "drive":40, "bus":30}
        commute_time = total_length / 1000 / speed_kmh[transport] * 60  # 분 단위
        st.success(f"총 거리: {round(total_length,1)} m, 예상 소요시간: {round(commute_time,1)} 분")
