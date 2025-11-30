import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import requests
import datetime
from alarm import calculate_alarm_time
from route import find_optimal_route, build_graph

st.set_page_config(page_title="스마트 통학 도우미", layout="wide")

st.title("🚍 스마트 통학 도우미")

st.header("📍 출발 / 도착 위치 입력")
start = st.text_input("출발지 입력 (예: 서울역)")
end = st.text_input("도착지 입력 (예: 고려대학교)")

prep_time = st.number_input("준비 시간(분)", min_value=0, value=30)

transport = st.selectbox(
    "이동수단 선택",
    ["버스", "지하철", "도보", "자전거"]
)

if st.button("최적 경로 계산"):
    with st.spinner("경로 탐색 중..."):

        graph = build_graph(transport)

        route, total_time = find_optimal_route(graph, start, end)
        st.success(f"📌 예상 이동시간: {total_time}분")

        alarm_time = calculate_alarm_time(prep_time, total_time)
        st.success(f"⏰ 기상 알람 시간: {alarm_time}")

        # 지도 출력
        geolocator = Nominatim(user_agent="commute")
        start_loc = geolocator.geocode(start)
        end_loc = geolocator.geocode(end)

        m = folium.Map(location=[start_loc.latitude, start_loc.longitude], zoom_start=14)
        folium.Marker([start_loc.latitude, start_loc.longitude], tooltip="출발").add_to(m)
        folium.Marker([end_loc.latitude, end_loc.longitude], tooltip="도착").add_to(m)
        st_folium(m, width=900, height=600)

