"""
visualizacao.py — Visualização da Rede com NetworkX

Gera 3 visualizações salvas em PNG:

    1. Mapa geográfico da rede completa (posição real das paradas)
    2. Grafo dos hubs (paradas com grau >= 10, layout por importância)
    3. Subgrafo de um caminho BFS vs Dijkstra entre dois terminais
"""

import os
import sys

import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

sys.path.insert(0, os.path.dirname(__file__))

from loader import load_gtfs
from graph import Graph, build_graph
from algorithms import bfs_path, dijkstra_path

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data")

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Conversão: Graph → NetworkX DiGraph
# ---------------------------------------------------------------------------

def to_networkx(graph: Graph, node_filter: set[str] = None) -> nx.DiGraph:
    """
    Converte nosso Graph para um DiGraph do NetworkX.
    Se node_filter for informado, inclui apenas esses vértices e as
    arestas entre eles.
    """
    G = nx.DiGraph()

    for stop_id, stop in graph.vertices.items():
        if node_filter and stop_id not in node_filter:
            continue
        G.add_node(stop_id, name=stop.stop_name, lat=stop.lat, lon=stop.lon)

    for from_id, edges in graph.adjacency.items():
        if node_filter and from_id not in node_filter:
            continue
        for edge in edges:
            if node_filter and edge.to not in node_filter:
                continue
            G.add_edge(from_id, edge.to, weight=edge.weight, route=edge.route_name)

    return G


# ---------------------------------------------------------------------------
# Visualização 1 — Mapa geográfico da rede completa
# ---------------------------------------------------------------------------

def plot_mapa_geografico(graph: Graph) -> str:
    print("  Gerando mapa geográfico...")

    nos_ativos = {v for v in graph.vertices if graph.out_degree(v) >= 1}
    G = to_networkx(graph, node_filter=nos_ativos)

    node_list = list(G.nodes())
    pos = {n: (G.nodes[n]["lon"], G.nodes[n]["lat"]) for n in node_list}
    graus = dict(G.degree())

    tamanhos = [max(5, graus[n] * 1.5) for n in node_list]
    nc = [graus[n] for n in node_list]

    fig, ax = plt.subplots(figsize=(14, 10))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#0f1117")

    nx.draw_networkx_edges(
        G, pos, ax=ax,
        edge_color="#3a6186", alpha=0.25, width=0.4, arrows=False,
    )

    nx.draw_networkx_nodes(
        G, pos, nodelist=node_list, ax=ax,
        node_size=tamanhos, node_color=nc,
        cmap=plt.cm.plasma, alpha=0.85,
    )

    # Destaca os 5 maiores hubs com label
    top5 = sorted(graus.items(), key=lambda x: x[1], reverse=True)[:5]
    top5_ids = [n for n, _ in top5 if n in pos]
    top5_pos    = {n: pos[n] for n in top5_ids}
    top5_labels = {n: graph.vertices[n].stop_name.split(",")[0] for n in top5_ids}

    nx.draw_networkx_nodes(
        G, top5_pos, nodelist=top5_ids, ax=ax,
        node_size=[graus[n] * 6 for n in top5_ids],
        node_color="#f5a623", alpha=1.0,
    )
    nx.draw_networkx_labels(
        G, top5_pos, labels=top5_labels, ax=ax,
        font_size=7, font_color="white", font_weight="bold",
    )

    ax.set_title("Rede de Transporte Público — ETUFOR · Fortaleza-CE",
                 color="white", fontsize=14, pad=12)
    ax.set_xlabel("Longitude", color="#aaaaaa", fontsize=9)
    ax.set_ylabel("Latitude",  color="#aaaaaa", fontsize=9)
    ax.tick_params(colors="#aaaaaa")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333333")

    legend = [
        mpatches.Patch(color="#f5a623", label="Terminais principais"),
        mpatches.Patch(color="#7b2d8b", label="Paradas comuns"),
    ]
    ax.legend(handles=legend, facecolor="#1a1a2e", labelcolor="white",
              fontsize=8, loc="lower left")

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "1_mapa_geografico.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Salvo: {path}")
    return path


# ---------------------------------------------------------------------------
# Visualização 2 — Grafo dos hubs (paradas mais conectadas)
# ---------------------------------------------------------------------------

def plot_grafo_hubs(graph: Graph, min_grau: int = 10) -> str:
    print(f"  Gerando grafo dos hubs (grau >= {min_grau})...")

    nos_hubs = {v for v in graph.vertices if graph.out_degree(v) >= min_grau}
    G = to_networkx(graph, node_filter=nos_hubs)

    node_list = list(G.nodes())
    graus     = dict(G.degree())
    tamanhos  = [graus[n] * 12 for n in node_list]
    nc        = [graus[n] for n in node_list]

    pos = nx.spring_layout(G, seed=42, k=1.8)

    fig, ax = plt.subplots(figsize=(14, 10))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#0f1117")

    nx.draw_networkx_edges(
        G, pos, ax=ax,
        edge_color="#4a90d9", alpha=0.3, width=0.8,
        arrows=True, arrowsize=8,
        connectionstyle="arc3,rad=0.1",
    )

    nx.draw_networkx_nodes(
        G, pos, nodelist=node_list, ax=ax,
        node_size=tamanhos, node_color=nc,
        cmap=plt.cm.YlOrRd, alpha=0.95,
    )

    # Labels apenas para os top 15
    top15 = sorted(graus.items(), key=lambda x: x[1], reverse=True)[:15]
    labels = {n: graph.vertices[n].stop_name.split(",")[0][:25] for n, _ in top15 if n in pos}
    nx.draw_networkx_labels(
        G, pos, labels=labels, ax=ax,
        font_size=6.5, font_color="white",
    )

    ax.set_title(
        f"Hubs da Rede — Paradas com grau ≥ {min_grau}  ({len(nos_hubs)} vértices)",
        color="white", fontsize=13, pad=12,
    )
    ax.axis("off")

    sm = plt.cm.ScalarMappable(cmap=plt.cm.YlOrRd,
                               norm=plt.Normalize(min(nc), max(nc)))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label("Grau total", color="white", fontsize=9)
    cbar.ax.yaxis.set_tick_params(color="white")
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="white")

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "2_grafo_hubs.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Salvo: {path}")
    return path


# ---------------------------------------------------------------------------
# Visualização 3 — BFS vs Dijkstra entre dois terminais
# ---------------------------------------------------------------------------

def plot_bfs_vs_dijkstra(graph: Graph, start_id: str, end_id: str) -> str:
    print("  Gerando comparativo BFS vs Dijkstra...")

    path_bfs         = bfs_path(graph, start_id, end_id)
    path_dijk, custo = dijkstra_path(graph, start_id, end_id)

    if not path_bfs or not path_dijk:
        print("  Sem caminho encontrado para essa comparação.")
        return ""

    todos_nos = set(path_bfs) | set(path_dijk)
    G = to_networkx(graph, node_filter=todos_nos)

    pos = {n: (graph.vertices[n].lon, graph.vertices[n].lat) for n in G.nodes()}

    fig, ax = plt.subplots(figsize=(14, 9))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#0f1117")

    edges_bfs   = list(zip(path_bfs[:-1],  path_bfs[1:]))
    edges_dijk  = list(zip(path_dijk[:-1], path_dijk[1:]))
    edges_comum = set(map(tuple, edges_bfs)) & set(map(tuple, edges_dijk))

    edges_so_bfs  = [e for e in edges_bfs  if tuple(e) not in edges_comum]
    edges_so_dijk = [e for e in edges_dijk if tuple(e) not in edges_comum]

    nx.draw_networkx_edges(G, pos, edgelist=list(edges_comum),
                           edge_color="#aaaaaa", width=2.5, ax=ax, alpha=0.6, arrows=False)
    nx.draw_networkx_edges(G, pos, edgelist=edges_so_bfs,
                           edge_color="#4fc3f7", width=2.0, ax=ax, alpha=0.85, arrows=False)
    nx.draw_networkx_edges(G, pos, edgelist=edges_so_dijk,
                           edge_color="#ef5350", width=2.0, ax=ax, alpha=0.85, arrows=False)

    nos_so_bfs  = list(set(path_bfs)  - set(path_dijk))
    nos_so_dijk = list(set(path_dijk) - set(path_bfs))
    nos_comuns  = list((set(path_bfs) & set(path_dijk)) - {start_id, end_id})

    nx.draw_networkx_nodes(G, pos, nodelist=nos_comuns,
                           node_color="#aaaaaa", node_size=40, ax=ax)
    nx.draw_networkx_nodes(G, pos, nodelist=nos_so_bfs,
                           node_color="#4fc3f7", node_size=50, ax=ax)
    nx.draw_networkx_nodes(G, pos, nodelist=nos_so_dijk,
                           node_color="#ef5350", node_size=50, ax=ax)
    nx.draw_networkx_nodes(G, pos, nodelist=[start_id, end_id],
                           node_color="#f5a623", node_size=200, ax=ax)

    labels_od = {
        start_id: graph.vertices[start_id].stop_name.split(",")[0],
        end_id:   graph.vertices[end_id].stop_name.split(",")[0],
    }
    nx.draw_networkx_labels(G, pos, labels=labels_od, ax=ax,
                            font_size=7, font_color="white", font_weight="bold")

    custo_bfs = sum(
        next((e.weight for e in graph.neighbors(u) if e.to == v), 0)
        for u, v in edges_bfs
    )

    ax.set_title(
        f"BFS vs Dijkstra — {graph.vertices[start_id].stop_name.split(',')[0]}"
        f" → {graph.vertices[end_id].stop_name.split(',')[0]}",
        color="white", fontsize=12, pad=12,
    )

    legend = [
        mpatches.Patch(color="#4fc3f7",
                       label=f"BFS  ({len(path_bfs)} paradas · custo {custo_bfs:.1f})"),
        mpatches.Patch(color="#ef5350",
                       label=f"Dijkstra ({len(path_dijk)} paradas · custo {custo:.1f})"),
        mpatches.Patch(color="#aaaaaa", label="Trecho compartilhado"),
        mpatches.Patch(color="#f5a623", label="Origem / Destino"),
    ]
    ax.legend(handles=legend, facecolor="#1a1a2e", labelcolor="white",
              fontsize=8, loc="upper left")

    ax.set_xlabel("Longitude", color="#aaaaaa", fontsize=8)
    ax.set_ylabel("Latitude",  color="#aaaaaa", fontsize=8)
    ax.tick_params(colors="#aaaaaa")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333333")

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "3_bfs_vs_dijkstra.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Salvo: {path}")
    return path


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------

def run_all_visualizations(graph: Graph) -> None:
    print("\n=== Visualizações NetworkX ===\n")
    plot_mapa_geografico(graph)
    plot_grafo_hubs(graph, min_grau=10)
    plot_bfs_vs_dijkstra(graph, start_id="5822", end_id="6079")
    print("\nTodas as imagens salvas na pasta /output")


if __name__ == "__main__":
    gtfs  = load_gtfs(DATA_DIR)
    graph = build_graph(gtfs)
    run_all_visualizations(graph)