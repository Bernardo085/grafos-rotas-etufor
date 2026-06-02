"""
analysis.py — Análises Estruturais do Grafo

Realiza as análises exigidas pelo roteiro:
    1. Grau dos vértices (entrada e saída)
    2. Conectividade (componentes e vértices isolados)
    3. Detecção de ciclos
    4. Vértices mais importantes (hubs)
    5. Comparativo BFS vs Dijkstra
"""

from algorithms import bfs, bfs_reachable, bfs_path, dijkstra_path, format_path
from graph import Graph


# ---------------------------------------------------------------------------
# 1. Grau dos vértices
# ---------------------------------------------------------------------------

def analyze_degrees(graph: Graph) -> dict:
    """
    Calcula grau de entrada e saída de todos os vértices.
    Retorna estatísticas gerais e os extremos (maior/menor grau).
    """
    out_degrees = {v: graph.out_degree(v) for v in graph.vertices}

    # Grau de entrada: conta quantas arestas chegam em cada vértice
    in_degrees = {v: 0 for v in graph.vertices}
    for edges in graph.adjacency.values():
        for edge in edges:
            in_degrees[edge.to] += 1

    total = len(graph.vertices)
    avg_out = sum(out_degrees.values()) / total
    avg_in  = sum(in_degrees.values()) / total

    top_out = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)[:5]
    top_in  = sorted(in_degrees.items(),  key=lambda x: x[1], reverse=True)[:5]
    isolated = [v for v in graph.vertices if out_degrees[v] == 0 and in_degrees[v] == 0]

    return {
        "out_degrees": out_degrees,
        "in_degrees":  in_degrees,
        "avg_out":     round(avg_out, 2),
        "avg_in":      round(avg_in, 2),
        "top_out":     top_out,
        "top_in":      top_in,
        "isolated":    isolated,
        "max_out":     max(out_degrees.values()),
        "max_in":      max(in_degrees.values()),
    }


def print_degree_analysis(graph: Graph, result: dict) -> None:
    print("=" * 55)
    print("ANÁLISE 1 — Grau dos Vértices")
    print("=" * 55)
    print(f"  Grau médio de saída  : {result['avg_out']}")
    print(f"  Grau médio de entrada: {result['avg_in']}")
    print(f"  Maior grau de saída  : {result['max_out']}")
    print(f"  Maior grau de entrada: {result['max_in']}")
    print(f"  Vértices isolados    : {len(result['isolated'])}")

    print("\n  Top 5 paradas com mais conexões de SAÍDA:")
    for stop_id, deg in result["top_out"]:
        name = graph.vertices[stop_id].stop_name
        print(f"    [{stop_id:>5}] {name:<40} grau={deg}")

    print("\n  Top 5 paradas com mais conexões de ENTRADA:")
    for stop_id, deg in result["top_in"]:
        name = graph.vertices[stop_id].stop_name
        print(f"    [{stop_id:>5}] {name:<40} grau={deg}")


# ---------------------------------------------------------------------------
# 2. Conectividade
# ---------------------------------------------------------------------------

def analyze_connectivity(graph: Graph) -> dict:
    """
    Identifica componentes fracamente conectados usando BFS repetido.

    Um componente é um grupo de vértices que se alcançam mutuamente.
    Vértices não alcançados por nenhuma viagem ficam em componentes isolados.
    """
    visited  = set()
    components = []

    for start in graph.vertices:
        if start in visited:
            continue
        reachable = bfs_reachable(graph, start)
        components.append(reachable)
        visited.update(reachable)

    components.sort(key=len, reverse=True)

    main_component   = components[0]
    small_components = [c for c in components if len(c) == 1]
    other_components = [c for c in components if 1 < len(c) < len(main_component)]

    return {
        "total_components":  len(components),
        "main_component":    main_component,
        "main_size":         len(main_component),
        "small_components":  small_components,
        "other_components":  other_components,
        "coverage_pct":      round(len(main_component) / graph.vertex_count() * 100, 1),
    }


def print_connectivity_analysis(graph: Graph, result: dict) -> None:
    print("\n" + "=" * 55)
    print("ANÁLISE 2 — Conectividade")
    print("=" * 55)
    print(f"  Componentes encontrados      : {result['total_components']}")
    print(f"  Componente principal         : {result['main_size']:,} vértices "
          f"({result['coverage_pct']}% da rede)")
    print(f"  Componentes isolados (1 nó)  : {len(result['small_components'])}")
    print(f"  Outros componentes           : {len(result['other_components'])}")

    if result["other_components"]:
        print("\n  Componentes secundários:")
        for comp in result["other_components"][:5]:
            sample = list(comp)[:2]
            names  = [graph.vertices[s].stop_name[:30] for s in sample]
            print(f"    {len(comp)} vértices — ex: {', '.join(names)}")


# ---------------------------------------------------------------------------
# 3. Detecção de ciclos
# ---------------------------------------------------------------------------

def analyze_cycles(graph: Graph) -> dict:
    """
    Detecta a existência de ciclos usando DFS com marcação de estados.

    Estados de cada vértice durante a DFS:
        0 → não visitado
        1 → em processamento (na pilha de chamadas)
        2 → completamente processado

    Se durante a DFS encontrarmos uma aresta para um vértice em estado 1,
    encontramos um ciclo (aresta de retorno).
    """
    state    = {v: 0 for v in graph.vertices}
    has_cycle = False
    cycle_example = []

    def dfs(v, path):
        nonlocal has_cycle
        if has_cycle:
            return

        state[v] = 1
        path.append(v)

        for edge in graph.neighbors(v):
            if state[edge.to] == 1:
                # Aresta de retorno — ciclo encontrado
                has_cycle = True
                idx = path.index(edge.to)
                cycle_example.extend(path[idx:] + [edge.to])
                return
            if state[edge.to] == 0:
                dfs(edge.to, path)

        state[v] = 2
        path.pop()

    # Percorre todos os vértices para cobrir componentes desconexos
    for v in graph.vertices:
        if state[v] == 0 and not has_cycle:
            dfs(v, [])

    return {
        "has_cycle":     has_cycle,
        "cycle_example": cycle_example,
    }


def print_cycle_analysis(graph: Graph, result: dict) -> None:
    print("\n" + "=" * 55)
    print("ANÁLISE 3 — Detecção de Ciclos")
    print("=" * 55)

    if result["has_cycle"]:
        print("  O grafo CONTÉM ciclos.")
        example = result["cycle_example"]
        if example:
            print(f"\n  Exemplo de ciclo detectado ({len(example)} paradas):")
            for stop_id in example[:6]:
                name = graph.vertices[stop_id].stop_name
                print(f"    → [{stop_id}] {name}")
            if len(example) > 6:
                print(f"    ... (+{len(example)-6} paradas)")
    else:
        print("  O grafo NÃO contém ciclos (é um DAG).")


# ---------------------------------------------------------------------------
# 4. Hubs — vértices mais importantes
# ---------------------------------------------------------------------------

def analyze_hubs(graph: Graph, degree_result: dict, top_n: int = 10) -> dict:
    """
    Identifica os hubs da rede: paradas com maior combinação de
    grau de entrada + saída (grau total), que representam os
    pontos de maior movimento e conexão da rede.
    """
    total_degree = {
        v: degree_result["in_degrees"][v] + degree_result["out_degrees"][v]
        for v in graph.vertices
    }
    hubs = sorted(total_degree.items(), key=lambda x: x[1], reverse=True)[:top_n]

    return {"hubs": hubs, "total_degree": total_degree}


def print_hub_analysis(graph: Graph, result: dict) -> None:
    print("\n" + "=" * 55)
    print("ANÁLISE 4 — Hubs (Paradas Mais Importantes)")
    print("=" * 55)
    print(f"  {'Parada':<45} {'Grau':>5}")
    print(f"  {'-'*45} {'-'*5}")
    for stop_id, deg in result["hubs"]:
        name = graph.vertices[stop_id].stop_name
        print(f"  {name:<45} {deg:>5}")


# ---------------------------------------------------------------------------
# 5. Comparativo BFS vs Dijkstra
# ---------------------------------------------------------------------------

def analyze_bfs_vs_dijkstra(graph: Graph, start_id: str, end_id: str) -> dict:
    """
    Compara os resultados do BFS e do Dijkstra para o mesmo par de paradas.

    BFS   → minimiza número de paradas (sem considerar peso)
    Dijkstra → minimiza custo total (tempo ou distância)

    A diferença entre os dois caminhos ilustra o trade-off entre
    conveniência (menos paradas) e eficiência (menor tempo).
    """
    path_bfs  = bfs_path(graph, start_id, end_id)
    path_dijk, cost_dijk = dijkstra_path(graph, start_id, end_id)

    # Calcula o custo real do caminho BFS para comparar
    cost_bfs = 0.0
    if path_bfs:
        for i in range(len(path_bfs) - 1):
            u, v = path_bfs[i], path_bfs[i + 1]
            edge = next((e for e in graph.neighbors(u) if e.to == v), None)
            if edge:
                cost_bfs += edge.weight

    return {
        "start_id":   start_id,
        "end_id":     end_id,
        "path_bfs":   path_bfs,
        "path_dijk":  path_dijk,
        "cost_bfs":   round(cost_bfs, 4),
        "cost_dijk":  round(cost_dijk, 4),
    }


def print_bfs_vs_dijkstra(graph: Graph, result: dict) -> None:
    start = graph.vertices[result["start_id"]].stop_name
    end   = graph.vertices[result["end_id"]].stop_name

    print("\n" + "=" * 55)
    print("ANÁLISE 5 — BFS vs Dijkstra")
    print("=" * 55)
    print(f"  Origem : {start}")
    print(f"  Destino: {end}\n")

    path_bfs  = result["path_bfs"]
    path_dijk = result["path_dijk"]

    print("  BFS (menor número de paradas):")
    if path_bfs:
        print(f"    Paradas no caminho : {len(path_bfs)}")
        print(f"    Custo real         : {result['cost_bfs']}")
    else:
        print("    Sem caminho encontrado.")

    print("\n  Dijkstra (menor custo):")
    if path_dijk:
        print(f"    Paradas no caminho : {len(path_dijk)}")
        print(f"    Custo total        : {result['cost_dijk']}")
    else:
        print("    Sem caminho encontrado.")

    if path_bfs and path_dijk:
        paradas_a_mais = len(path_dijk) - len(path_bfs)
        custo_economizado = round(result["cost_bfs"] - result["cost_dijk"], 4)
        print(f"\n  Dijkstra usa {abs(paradas_a_mais)} paradas a mais,")
        print(f"  mas economiza {custo_economizado} unidades de custo.")


# ---------------------------------------------------------------------------
# Execução completa de todas as análises
# ---------------------------------------------------------------------------

def run_all(graph: Graph, start_id: str, end_id: str) -> None:
    degrees     = analyze_degrees(graph)
    connectivity = analyze_connectivity(graph)
    cycles      = analyze_cycles(graph)
    hubs        = analyze_hubs(graph, degrees)
    comparison  = analyze_bfs_vs_dijkstra(graph, start_id, end_id)

    print_degree_analysis(graph, degrees)
    print_connectivity_analysis(graph, connectivity)
    print_cycle_analysis(graph, cycles)
    print_hub_analysis(graph, hubs)
    print_bfs_vs_dijkstra(graph, comparison)