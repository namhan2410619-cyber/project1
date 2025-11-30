import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable
from route import build_graph, find_optimal_route
from alarm import calculate_alarm_time

st.set_page_config(page_title="스마트 통학 도우미", layout="wide")
st.title("🚍 스마트 통학 알람 & 경로 지도")

# ----------------------
# 사용자 입력
# ----------------------
start = st.text_input("출발지", "서울역")
end = st.text_input("도착지", "고려대학교")
prep_time = st.number_input("준비 시간 (분)", min_value=0, value=30)
transport = st.selectbox("이동수단 선택", ["도보", "버스", "지하철", "자전거"])
school_hour = st.number_input("등교 시간 - 시", min_value=0, max_value=23, value=9)
school_minute = st.number_input("등교 시간 - 분", min_value=0, max_value=59, value=0)

# ----------------------
# 최적 경로 계산
# ----------------------
if st.button("경로 계산 & 알람 시간"):

    graph = build_graph(transport)
    route, total_time = find_optimal_route(graph, start, end)
    
    alarm_time = calculate_alarm_time(prep_time, total_time, school_hour, school_minute)
    
    st.success(f"예상 이동 시간: {total_time} 분")
    st.info(f"추천 기상 시간: {alarm_time}")
    st.info(f"추천 경로: {' → '.join(route)}")

    # ----------------------
    # 지도 표시
    # ----------------------
    geolocator = Nominatim(user_agent="commute_app")
    try:
        start_loc = geolocator.geocode(start)
        end_loc = geolocator.geocode(end)

        if not start_loc or not end_loc:
            st.error("주소를 찾을 수 없습니다. 정확히 입력해주세요.")
        else:
            m = folium.Map(location=[(start_loc.latitude + end_loc.latitude)/2,
                                     (start_loc.longitude + end_loc.longitude)/2], zoom_start=14)
            folium.Marker([start_loc.latitude, start_loc.longitude], tooltip="출발지", popup=start).add_to(m)
            folium.Marker([end_loc.latitude, end_loc.longitude], tooltip="도착지", popup=end).add_to(m)

            st_folium(m, width=900, height=600)
            
    except GeocoderUnavailable:
        st.error("Nominatim 서버에 연결할 수 없습니다. 인터넷 연결을 확인해주세요.")
