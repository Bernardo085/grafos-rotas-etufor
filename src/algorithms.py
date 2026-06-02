"""
algorithms.py — Algoritmos Clássicos de Grafos

Implementações do zero (sem bibliotecas externas):
    - BFS  (Busca em Largura)
    - Dijkstra (Caminho Mínimo)
"""

from collections import deque
from graph import Graph


# ---------------------------------------------------------------------------
# BFS — Busca em Largura
# ---------------------------------------------------------------------------

def bfs(graph: Graph, start_id: str) -> dict[str, str | None]:
    """
    Percorre o grafo a partir de start_id em largura (nível por nível).

    Retorna um dicionário de predecessores {stop_id: predecessor},
    que permite reconstruir o caminho até qualquer vértice visitado.
    Um valor None indica que o vértice é a origem.

    Complexidade: O(V + E)
    """
    if start_id not in graph.vertices:
        raise ValueError(f"Parada '{start_id}' não existe no grafo.")

    visitados   = {start_id}
    predecessores = {start_id: None}
    fila        = deque([start_id])

    while fila:
        atual = fila.popleft()
        for edge in graph.neighbors(atual):
            if edge.to not in visitados:
                visitados.add(edge.to)
                predecessores[edge.to] = atual
                fila.append(edge.to)

    return predecessores


def bfs_path(graph: Graph, start_id: str, end_id: str) -> list[str] | None:
    """
    Encontra o caminho com menor número de paradas entre start e end.
    Retorna a lista de stop_ids do caminho, ou None se não houver conexão.
    """
    predecessores = bfs(graph, start_id)

    if end_id not in predecessores:
        return None

    # Reconstrói o caminho de trás para frente
    caminho = []
    atual = end_id
    while atual is not None:
        caminho.append(atual)
        atual = predecessores[atual]

    caminho.reverse()
    return caminho


def bfs_reachable(graph: Graph, start_id: str) -> set[str]:
    """Retorna o conjunto de todos os vértices alcançáveis a partir de start_id."""
    return set(bfs(graph, start_id).keys())


# ---------------------------------------------------------------------------
# Dijkstra — Caminho Mínimo por Peso
# ---------------------------------------------------------------------------

def dijkstra(graph: Graph, start_id: str) -> tuple[dict[str, float], dict[str, str | None]]:
    """
    Calcula o caminho de menor peso a partir de start_id para todos os vértices.

    Usa uma fila de prioridade manual com lista ordenada (heap simples).
    Adequado para grafos com pesos não-negativos.

    Retorna:
        distancias   → {stop_id: menor custo acumulado até ele}
        predecessores → {stop_id: predecessor no caminho ótimo}

    Complexidade: O((V + E) log V)
    """
    if start_id not in graph.vertices:
        raise ValueError(f"Parada '{start_id}' não existe no grafo.")

    import heapq

    INF = float("inf")
    distancias    = {v: INF for v in graph.vertices}
    predecessores = {v: None for v in graph.vertices}
    distancias[start_id] = 0

    # Fila de prioridade: (custo_acumulado, stop_id)
    heap = [(0, start_id)]

    while heap:
        custo_atual, u = heapq.heappop(heap)

        # Vértice já processado com custo menor — ignora
        if custo_atual > distancias[u]:
            continue

        for edge in graph.neighbors(u):
            novo_custo = distancias[u] + edge.weight
            if novo_custo < distancias[edge.to]:
                distancias[edge.to]    = novo_custo
                predecessores[edge.to] = u
                heapq.heappush(heap, (novo_custo, edge.to))

    return distancias, predecessores


def dijkstra_path(
    graph: Graph,
    start_id: str,
    end_id: str,
) -> tuple[list[str] | None, float]:
    """
    Retorna o caminho de menor peso entre start e end.

    Retorna:
        caminho → lista de stop_ids (ou None se não houver caminho)
        custo   → peso total do caminho (ou inf se não alcançável)
    """
    distancias, predecessores = dijkstra(graph, start_id)

    custo = distancias.get(end_id, float("inf"))
    if custo == float("inf"):
        return None, float("inf")

    # Reconstrói o caminho de trás para frente
    caminho = []
    atual = end_id
    while atual is not None:
        caminho.append(atual)
        atual = predecessores[atual]

    caminho.reverse()
    return caminho, round(custo, 4)


# ---------------------------------------------------------------------------
# Utilitário: formata caminho para exibição
# ---------------------------------------------------------------------------

def format_path(graph: Graph, path: list[str], weight_unit: str = "") -> None:
    """Imprime um caminho de forma legível, parada por parada."""
    if not path:
        print("  Nenhum caminho encontrado.")
        return

    for i, stop_id in enumerate(path):
        stop = graph.vertices[stop_id]
        prefix = "  Início →" if i == 0 else ("  Fim    →" if i == len(path) - 1 else f"  Parada {i:>2} →")
        print(f"{prefix} [{stop_id}] {stop.stop_name}")

    if weight_unit:
        print(f"  Total de paradas intermediárias: {len(path) - 2}")