# api.py
def get_bus_eta(station_id):
    """
    station_id: 출발지 정류장 ID
    return: 샘플 버스 ETA (분 단위)
    """
    return 5  # 다음 버스 5분 후 도착

def get_subway_eta(station_name):
    """
    station_name: 출발역 이름
    return: 샘플 지하철 ETA (분 단위)
    """
    return 3  # 다음 열차 3분 후 도착

def get_car_eta(origin, destination):
    """
    origin, destination: (lat, lon)
    return: 차량 예상 소요 시간 (분 단위, 샘플)
    """
    return 15  # 차량 예상 소요 15분
