from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import folium
import time
from route import build_graph, find_optimal_route

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/route")
def route(
    request: Request,
    transport: str = Form(...),
    start_lat: float = Form(...),
    start_lon: float = Form(...),
    end_lat: float = Form(...),
    end_lon: float = Form(...)
):
    start_time = time.time()

    G = build_graph(start_lat, start_lon, transport)
    route_nodes, total_length = find_optimal_route(G, (start_lat, start_lon), (end_lat, end_lon))

    if not route_nodes:
        return {"error": "경로 계산 실패"}

    route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for i, n in enumerate(route_nodes) if i % 3 == 0]

    m = folium.Map(location=[start_lat, start_lon], zoom_start=14)
    folium.Marker([start_lat, start_lon], tooltip="출발지").add_to(m)
    folium.Marker([end_lat, end_lon], tooltip="도착지", icon=folium.Icon(color="red")).add_to(m)
    folium.PolyLine(route_coords, weight=5).add_to(m)

    exec_time = round(time.time() - start_time, 2)
    eta_min = round(total_length / 80, 1)

    html_map = m._repr_html_()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "map": html_map,
        "exec_time": exec_time,
        "eta_min": eta_min,
        "distance": round(total_length, 1)
    })
