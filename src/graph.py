"""
graph.py — Construção do Grafo de Transporte Público

Modela a rede de ônibus como um dígrafo ponderado:
    Vértices → paradas de ônibus
    Arestas  → conexão direta entre duas paradas consecutivas em uma viagem
    Peso     → tempo de viagem em minutos (ou distância em km como fallback)
"""

import math
from dataclasses import dataclass
from loader import GTFSData, Stop, parse_time_to_minutes, get_route_name


@dataclass
class Edge:
    to: str          # stop_id de destino
    weight: float    # custo da aresta (minutos ou km)
    weight_type: str # "tempo_min" ou "distancia_km"
    trip_id: str
    route_name: str


class Graph:
    """Dígrafo ponderado com lista de adjacência."""

    def __init__(self):
        self.vertices: dict[str, Stop] = {}
        self.adjacency: dict[str, list[Edge]] = {}
        self._edges_by_time = 0
        self._edges_by_distance = 0

    def add_vertex(self, stop: Stop) -> None:
        if stop.stop_id not in self.vertices:
            self.vertices[stop.stop_id] = stop
            self.adjacency[stop.stop_id] = []

    def add_edge(self, from_id: str, edge: Edge) -> None:
        for existing in self.adjacency[from_id]:
            if existing.to == edge.to and existing.trip_id == edge.trip_id:
                return
        self.adjacency[from_id].append(edge)

    def neighbors(self, stop_id: str) -> list[Edge]:
        return self.adjacency.get(stop_id, [])

    def vertex_count(self) -> int:
        return len(self.vertices)

    def edge_count(self) -> int:
        return sum(len(edges) for edges in self.adjacency.values())

    def out_degree(self, stop_id: str) -> int:
        return len(self.adjacency.get(stop_id, []))

    def in_degree(self, stop_id: str) -> int:
        return sum(1 for edges in self.adjacency.values() for e in edges if e.to == stop_id)

    def summary(self) -> None:
        print("=== Grafo ===")
        print(f"  Vértices : {self.vertex_count():>8,}")
        print(f"  Arestas  : {self.edge_count():>8,}")
        print(f"    peso por tempo     : {self._edges_by_time:>7,}")
        print(f"    peso por distância : {self._edges_by_distance:>7,}")
        print(f"  Tipo     : Dígrafo ponderado / Lista de adjacência")


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância em km entre dois pontos geográficos (fórmula de Haversine)."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def _calculate_weight(u, v, stop_u: Stop, stop_v: Stop):
    """
    Calcula o peso da aresta entre duas paradas consecutivas.
    Prioridade 1 → diferença de horário (minutos)
    Prioridade 2 → distância geográfica Haversine (km)
    """
    dep = parse_time_to_minutes(u.departure_time or "")
    arr = parse_time_to_minutes(v.arrival_time or "")

    if dep is not None and arr is not None and arr - dep > 0:
        return round(arr - dep, 4), "tempo_min"

    dist = haversine_km(stop_u.lat, stop_u.lon, stop_v.lat, stop_v.lon)
    if dist > 0:
        return round(dist, 4), "distancia_km"

    return None, None


def build_graph(gtfs: GTFSData) -> Graph:
    print("Construindo grafo...")
    graph = Graph()

    for stop in gtfs.stops.values():
        graph.add_vertex(stop)

    # Agrupa os registros de tempo por viagem (já vêm ordenados do loader)
    trips_stops: dict[str, list] = {}
    for st in gtfs.stop_times:
        trips_stops.setdefault(st.trip_id, []).append(st)

    # Acumula todos os pesos observados para cada par (route_id, u, v)
    # Estrutura: { (route_id, stop_u, stop_v): {"pesos": [], "weight_type": str, "route_name": str} }
    route_edges: dict[tuple, dict] = {}

    for trip_id, stop_seq in trips_stops.items():
        route_id   = gtfs.trips[trip_id].route_id
        route_name = get_route_name(gtfs, trip_id)

        for i in range(len(stop_seq) - 1):
            u = stop_seq[i]
            v = stop_seq[i + 1]

            stop_u = gtfs.stops.get(u.stop_id)
            stop_v = gtfs.stops.get(v.stop_id)
            if not stop_u or not stop_v:
                continue

            weight, weight_type = _calculate_weight(u, v, stop_u, stop_v)
            if weight is None:
                continue

            key = (route_id, u.stop_id, v.stop_id)
            if key not in route_edges:
                route_edges[key] = {"pesos": [], "weight_type": weight_type, "route_name": route_name}
            route_edges[key]["pesos"].append(weight)

    # Cria uma única aresta por (linha, u → v) usando a média dos pesos coletados
    for (route_id, from_id, to_id), data in route_edges.items():
        avg_weight = round(sum(data["pesos"]) / len(data["pesos"]), 4)
        weight_type = data["weight_type"]

        edge = Edge(
            to=to_id,
            weight=avg_weight,
            weight_type=weight_type,
            trip_id=route_id,
            route_name=data["route_name"],
        )
        graph.add_edge(from_id=from_id, edge=edge)

        if weight_type == "tempo_min":
            graph._edges_by_time += 1
        else:
            graph._edges_by_distance += 1

    print("Grafo construído!\n")
    graph.summary()
    return graph