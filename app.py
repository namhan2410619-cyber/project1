# app.py
import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from route import build_graph, find_optimal_route
from alarm import calculate_alarm_time
from api import get_bus_eta, get_subway_eta

st.set_page_config(page_title="스마트 통학 도우미", layout="wide")
st.title("🚍 스마트 통학 알람 & 지도 (완성판)")

start = st.text_input("출발지", "서울역")
end = st.text_input("도착지", "고려대학교")
prep_time = st.number_input("준비 시간 (분)", min_value=0, value=30)
transport = st.selectbox("이동수단 선택", ["walk", "bike", "drive", "bus", "subway"])
school_hour = st.number_input("등교 시간 - 시", min_value=0, max_value=23, value=9)
school_minute = st.number_input("등교 시간 - 분", min_value=0, max_value=59, value=0)

if st.button("최적 경로 & 알람 계산"):
    geolocator = Nominatim(user_agent="commute_app")

    start_loc_list = geolocator.geocode(start, exactly_one=False, limit=3)
    end_loc_list = geolocator.geocode(end, exactly_one=False, limit=3)

    if not start_loc_list or not end_loc_list:
        st.error("주소를 찾을 수 없습니다. 조금 더 정확히 입력해주세요.")
    else:
        start_loc = start_loc_list[0]
        end_loc = end_loc_list[0]

        start_point = (start_loc.latitude, start_loc.longitude)
        end_point = (end_loc.latitude, end_loc.longitude)

        transport_type = transport if transport in ['walk','bike','drive'] else 'drive'
        G = build_graph(start_point[0], start_point[1], transport_type)
        route_nodes, total_length = find_optimal_route(G, start_point, end_point)

        speed_kmh = {"walk":5, "bike":15, "drive":40, "bus":30, "subway":35}[transport]
        commute_time = total_length / 1000 / speed_kmh * 60

        if transport == "bus":
            commute_time += get_bus_eta()
        elif transport == "subway":
            commute_time += get_subway_eta()

        alarm_time = calculate_alarm_time(prep_time, commute_time, school_hour, school_minute)

        st.success(f"총 이동 거리: {total_length/1000:.2f} km")
        st.info(f"추천 기상 시간: {alarm_time}")
        st.info(f"예상 이동 시간: {commute_time:.0f} 분")

        if route_nodes:
            lats = [G.nodes[n]['y'] for n in route_nodes]
            lons = [G.nodes[n]['x'] for n in route_nodes]
            center_lat = sum(lats)/len(lats)
            center_lon = sum(lons)/len(lons)
        else:
            center_lat = (start_point[0]+end_point[0])/2
            center_lon = (start_point[1]+end_point[1])/2

        m = folium.Map(location=[center_lat, center_lon], zoom_start=14)
        folium.Marker([start_point[0], start_point[1]], tooltip="출발지", popup=start, icon=folium.Icon(color="green")).add_to(m)
        folium.Marker([end_point[0], end_point[1]], tooltip="도착지", popup=end, icon=folium.Icon(color="red")).add_to(m)

        if route_nodes:
            route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route_nodes]
            folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.7).add_to(m)

        st_folium(m, width=1000, height=600)
