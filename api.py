# api.py
import requests

# ----------------------
# 경기도 버스 API
# ----------------------
BUS_API_KEY = "518211951a7b55f01e56382c9c1af89ccbcb85fe5b170e5af6acc01ed897aa3f"

def get_bus_eta(bus_route_id=None, station_id=None):
    """
    bus_route_id: 버스 노선 ID
    station_id: 정류장 ID
    return: 다음 버스 도착 예정 시간 (분 단위)
    """
    if not bus_route_id or not station_id:
        # 샘플값 반환
        return 5
    url = f"https://apis.data.go.kr/6410000/busarrivalservice/v2/arrivalsByRoute?serviceKey={BUS_API_KEY}&busRouteId={bus_route_id}&stationId={station_id}"
    try:
        response = requests.get(url)
        data = response.json()
        eta_list = data.get('response', {}).get('busArrivalList', [])
        if eta_list:
            return int(eta_list[0].get('predictTime1', 0))
        else:
            return 0
    except Exception as e:
        print(f"버스 API 호출 오류: {e}")
        return 0

# ----------------------
# 서울시 지하철 실시간 API
# ----------------------
SUBWAY_API_KEY = "6763596c5a717a3033337a735a5559"

def get_subway_eta(line_no="1"):
    """
    line_no: 지하철 호선
    return: 다음 열차 도착 예정 시간(분 단위)
    """
    if not line_no:
        return 3
    url = f"http://swopenAPI.seoul.go.kr/api/subway/{SUBWAY_API_KEY}/xml/realtimePosition/0/5/{line_no}호선"
    try:
        response = requests.get(url)
        # XML 파싱 필요, 샘플로 3분 반환
        return 3
    except Exception as e:
        print(f"지하철 API 호출 오류: {e}")
        return 0
