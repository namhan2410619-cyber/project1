# api.py
import requests

# ----------------------
# 경기도 버스 API
# ----------------------
BUS_API_KEY = "518211951a7b55f01e56382c9c1af89ccbcb85fe5b170e5af6acc01ed897aa3f"

def get_bus_eta(bus_route_id, station_id):
    """
    bus_route_id: 버스 노선 ID
    station_id: 정류장 ID
    return: 다음 버스 도착 예정 시간 (분 단위)
    """
    url = f"https://apis.data.go.kr/6410000/busarrivalservice/v2/arrivalsByRoute?serviceKey={BUS_API_KEY}&busRouteId={bus_route_id}&stationId={station_id}"
    try:
        response = requests.get(url)
        data = response.json()
        eta_list = data.get('response', {}).get('busArrivalList', [])
        if eta_list:
            next_bus_min = int(eta_list[0].get('predictTime1', 0))
            return next_bus_min
        else:
            return 0
    except Exception as e:
        print(f"버스 API 호출 오류: {e}")
        return 0

# ----------------------
# 서울시 지하철 실시간 API
# ----------------------
SUBWAY_API_KEY = "6763596c5a717a3033337a735a5559"

def get_subway_eta(line_no="1", start_index=0, end_index=5):
    """
    line_no: 지하철 호선
    start_index, end_index: 가져올 데이터 범위
    return: 다음 열차 도착 예정 시간(분 단위) 리스트
    """
    url = f"http://swopenAPI.seoul.go.kr/api/subway/{SUBWAY_API_KEY}/xml/realtimePosition/{start_index}/{end_index}/{line_no}호선"
    try:
        response = requests.get(url)
        # XML 파싱 필요, 샘플로 다음 열차 3분으로 임시 반환
        # 실제 구현 시 xml.etree.ElementTree 등으로 도착시간 추출
        return 3
    except Exception as e:
        print(f"지하철 API 호출 오류: {e}")
        return 0
