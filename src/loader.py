"""
loader.py — Leitura dos arquivos GTFS da ETUFOR

Transforma os arquivos .txt em objetos Python prontos para uso.
Arquivos utilizados: stops, routes, trips, stop_times
"""

import csv
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Stop:
    stop_id: str
    stop_name: str
    lat: float
    lon: float


@dataclass
class StopTime:
    trip_id: str
    stop_id: str
    stop_sequence: int
    arrival_time: Optional[str]
    departure_time: Optional[str]


@dataclass
class Trip:
    trip_id: str
    route_id: str


@dataclass
class Route:
    route_id: str
    route_short_name: str
    route_long_name: str


@dataclass
class GTFSData:
    stops: dict[str, Stop] = field(default_factory=dict)
    trips: dict[str, Trip] = field(default_factory=dict)
    routes: dict[str, Route] = field(default_factory=dict)
    stop_times: list[StopTime] = field(default_factory=list)


def parse_time_to_minutes(time_str: str) -> Optional[float]:
    """
    Converte 'HH:MM:SS' para minutos desde meia-noite.
    Suporta horários acima de 24h (ex: 25:10:00), que o GTFS usa
    para viagens que passam da meia-noite sem trocar de dia.
    """
    if not time_str or time_str.strip() == "":
        return None
    parts = time_str.strip().split(":")
    if len(parts) != 3:
        return None
    try:
        h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
        return h * 60 + m + s / 60
    except ValueError:
        return None


def load_stops(filepath: str) -> dict[str, Stop]:
    stops = {}
    skipped = 0
    with open(filepath, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            try:
                lat = float(row["stop_lat"])
                lon = float(row["stop_lon"])
            except (ValueError, KeyError):
                skipped += 1
                continue
            stop_id = row["stop_id"].strip()
            stops[stop_id] = Stop(stop_id, row.get("stop_name", "").strip(), lat, lon)
    print(f"  [stops]      {len(stops):>6,} paradas    | {skipped} ignoradas")
    return stops


def load_routes(filepath: str) -> dict[str, Route]:
    routes = {}
    with open(filepath, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            route_id = row["route_id"].strip()
            routes[route_id] = Route(
                route_id,
                row.get("route_short_name", "").strip(),
                row.get("route_long_name", "").strip(),
            )
    print(f"  [routes]     {len(routes):>6,} linhas")
    return routes


def load_trips(filepath: str) -> dict[str, Trip]:
    trips = {}
    with open(filepath, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            trip_id = row["trip_id"].strip()
            trips[trip_id] = Trip(trip_id, row.get("route_id", "").strip())
    print(f"  [trips]      {len(trips):>6,} viagens")
    return trips


def load_stop_times(
    filepath: str,
    valid_stop_ids: set[str],
    valid_trip_ids: set[str],
) -> list[StopTime]:
    stop_times = []
    skipped = 0
    with open(filepath, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            trip_id = row["trip_id"].strip()
            stop_id = row["stop_id"].strip()
            if trip_id not in valid_trip_ids or stop_id not in valid_stop_ids:
                skipped += 1
                continue
            try:
                seq = int(row["stop_sequence"])
            except (ValueError, KeyError):
                skipped += 1
                continue
            stop_times.append(StopTime(
                trip_id=trip_id,
                stop_id=stop_id,
                stop_sequence=seq,
                arrival_time=row.get("arrival_time", "").strip() or None,
                departure_time=row.get("departure_time", "").strip() or None,
            ))

    # Ordenação essencial: garante que as paradas de cada viagem
    # estejam em sequência antes de gerar as arestas no graph.py
    stop_times.sort(key=lambda st: (st.trip_id, st.stop_sequence))
    print(f"  [stop_times] {len(stop_times):>6,} registros | {skipped} ignorados")
    return stop_times


def load_gtfs(data_dir: str) -> GTFSData:
    print(f"\nCarregando GTFS de: {os.path.abspath(data_dir)}")
    print("-" * 50)

    stops_path      = os.path.join(data_dir, "stops.txt")
    routes_path     = os.path.join(data_dir, "routes.txt")
    trips_path      = os.path.join(data_dir, "trips.txt")
    stop_times_path = os.path.join(data_dir, "stop_times.txt")

    for path in [stops_path, routes_path, trips_path, stop_times_path]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    stops  = load_stops(stops_path)
    routes = load_routes(routes_path)
    trips  = load_trips(trips_path)
    stop_times = load_stop_times(
        stop_times_path,
        valid_stop_ids=set(stops.keys()),
        valid_trip_ids=set(trips.keys()),
    )

    print("-" * 50)
    print("Carga concluída!\n")
    return GTFSData(stops=stops, trips=trips, routes=routes, stop_times=stop_times)


def get_route_name(gtfs: GTFSData, trip_id: str) -> str:
    trip = gtfs.trips.get(trip_id)
    if not trip:
        return "Linha desconhecida"
    route = gtfs.routes.get(trip.route_id)
    if not route:
        return f"Linha {trip.route_id}"
    name = route.route_short_name or route.route_id
    if route.route_long_name:
        name += f" - {route.route_long_name}"
    return name