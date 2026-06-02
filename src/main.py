"""
main.py — Interface Principal do Projeto

Menu interativo no terminal que demonstra todas as funcionalidades:
    1. Informações do grafo
    2. Buscar parada por nome
    3. Caminho com menos paradas entre dois pontos (BFS)
    4. Caminho mais rápido entre dois pontos (Dijkstra)
    5. Análises estruturais completas
    6. Gerar visualizações
    7. Sair
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from loader import load_gtfs
from graph import build_graph, Graph
from algorithms import bfs_path, dijkstra_path, format_path
from analysis import (
    analyze_degrees, analyze_connectivity, analyze_cycles,
    analyze_hubs, analyze_bfs_vs_dijkstra,
    print_degree_analysis, print_connectivity_analysis,
    print_cycle_analysis, print_hub_analysis, print_bfs_vs_dijkstra,
)
from visualizacao import run_all_visualizations

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


# ---------------------------------------------------------------------------
# Utilitários de terminal
# ---------------------------------------------------------------------------

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input("\n  Pressione Enter para continuar...")


def header(title: str) -> None:
    print("\n" + "=" * 55)
    print(f"  {title}")
    print("=" * 55)


def ask_stop(graph: Graph, label: str) -> str | None:
    """Pede um stop_id ao usuário e valida se existe no grafo."""
    value = input(f"\n  {label} (ID da parada): ").strip()
    if value not in graph.vertices:
        print(f"  ✗ Parada '{value}' não encontrada no grafo.")
        return None
    stop = graph.vertices[value]
    print(f"  ✓ {stop.stop_name}")
    return value


# ---------------------------------------------------------------------------
# Opções do menu
# ---------------------------------------------------------------------------

def menu_info(graph: Graph) -> None:
    header("Informações do Grafo")
    graph.summary()
    print()

    stops  = list(graph.vertices.values())
    routes = set()
    for edges in graph.adjacency.values():
        for e in edges:
            routes.add(e.route_name)

    print(f"  Linhas de ônibus ativas: {len(routes)}")
    print(f"\n  Amostra de paradas:")
    for stop in stops[:5]:
        print(f"    [{stop.stop_id:>5}] {stop.stop_name}")

    pause()


def menu_search_stop(graph: Graph) -> None:
    header("Buscar Parada por Nome")
    termo = input("\n  Digite parte do nome da parada: ").strip().upper()

    if not termo:
        print("  Termo vazio.")
        pause()
        return

    encontradas = [
        s for s in graph.vertices.values()
        if termo in s.stop_name.upper()
    ]

    if not encontradas:
        print("  Nenhuma parada encontrada.")
    else:
        print(f"\n  {len(encontradas)} parada(s) encontrada(s):\n")
        for s in encontradas[:20]:
            print(f"    [{s.stop_id:>5}] {s.stop_name}  (lat={s.lat}, lon={s.lon})")
        if len(encontradas) > 20:
            print(f"    ... (+{len(encontradas) - 20} resultados)")

    pause()


def menu_bfs(graph: Graph) -> None:
    header("Caminho com Menos Paradas — BFS")
    print("  Encontra o caminho com o menor número de paradas,")
    print("  sem considerar tempo ou distância.\n")

    start = ask_stop(graph, "Origem")
    if not start:
        pause()
        return
    end = ask_stop(graph, "Destino")
    if not end:
        pause()
        return

    print("\n  Calculando...")
    path = bfs_path(graph, start, end)

    if not path:
        print("\n  Não há caminho entre essas paradas.")
    else:
        print(f"\n  Caminho encontrado — {len(path)} paradas:\n")
        format_path(graph, path)

    pause()


def menu_dijkstra(graph: Graph) -> None:
    header("Caminho Mais Rápido — Dijkstra")
    print("  Encontra o caminho com o menor custo (tempo ou distância),")
    print("  podendo passar por mais paradas para chegar mais rápido.\n")

    start = ask_stop(graph, "Origem")
    if not start:
        pause()
        return
    end = ask_stop(graph, "Destino")
    if not end:
        pause()
        return

    print("\n  Calculando...")
    path, cost = dijkstra_path(graph, start, end)

    if not path:
        print("\n  Não há caminho entre essas paradas.")
    else:
        # Descobre a unidade predominante no caminho
        units = []
        for i in range(len(path) - 1):
            edge = next((e for e in graph.neighbors(path[i]) if e.to == path[i+1]), None)
            if edge:
                units.append(edge.weight_type)
        unit = "min" if units.count("tempo_min") >= len(units) / 2 else "km"

        print(f"\n  Caminho encontrado — {len(path)} paradas — custo total: {cost} {unit}\n")
        format_path(graph, path)

    pause()


def menu_analysis(graph: Graph) -> None:
    header("Análises Estruturais")
    print("  Escolha uma análise:\n")
    print("    [1] Grau dos vértices")
    print("    [2] Conectividade")
    print("    [3] Detecção de ciclos")
    print("    [4] Hubs (paradas mais importantes)")
    print("    [5] Comparativo BFS vs Dijkstra")
    print("    [6] Todas as análises")
    print("    [0] Voltar")

    choice = input("\n  Opção: ").strip()

    if choice == "0":
        return

    degrees      = None
    connectivity = None

    if choice in ("1", "6"):
        degrees = analyze_degrees(graph)
        print()
        print_degree_analysis(graph, degrees)

    if choice in ("2", "6"):
        print("\n  Calculando conectividade (pode demorar alguns segundos)...")
        connectivity = analyze_connectivity(graph)
        print_connectivity_analysis(graph, connectivity)

    if choice in ("3", "6"):
        print("\n  Detectando ciclos...")
        cycles = analyze_cycles(graph)
        print_cycle_analysis(graph, cycles)

    if choice in ("4", "6"):
        if degrees is None:
            degrees = analyze_degrees(graph)
        hubs = analyze_hubs(graph, degrees)
        print_hub_analysis(graph, hubs)

    if choice in ("5", "6"):
        header("Comparativo BFS vs Dijkstra")
        print("  Informe as paradas para a comparação:\n")
        start = ask_stop(graph, "Origem")
        if not start:
            pause()
            return
        end = ask_stop(graph, "Destino")
        if not end:
            pause()
            return
        print("\n  Calculando...")
        comparison = analyze_bfs_vs_dijkstra(graph, start, end)
        print_bfs_vs_dijkstra(graph, comparison)

    pause()



def menu_visualizacao(graph):
    header("Gerar Visualizações")
    print("  Serão geradas 3 imagens na pasta output/:")
    print("    1. Mapa geográfico da rede completa")
    print("    2. Grafo dos hubs (paradas mais conectadas)")
    print("    3. Comparativo BFS vs Dijkstra (Terminal Siqueira → Papicu)")
    print()
    confirm = input("  Confirmar? (s/n): ").strip().lower()
    if confirm != "s":
        print("  Cancelado.")
        pause()
        return
    print()
    run_all_visualizations(graph)
    pause()

# ---------------------------------------------------------------------------
# Loop principal
# ---------------------------------------------------------------------------

def main():
    clear()
    print("\n" + "=" * 55)
    print("  ANÁLISE DE REDE DE TRANSPORTE PÚBLICO — ETUFOR")
    print("  Trabalho Final — Teoria dos Grafos")
    print("=" * 55)
    print("\n  Carregando dados GTFS...\n")

    gtfs  = load_gtfs(DATA_DIR)
    graph = build_graph(gtfs)

    while True:
        print("\n" + "=" * 55)
        print("  MENU PRINCIPAL")
        print("=" * 55)
        print("  [1] Informações do grafo")
        print("  [2] Buscar parada por nome")
        print("  [3] Caminho com menos paradas (BFS)")
        print("  [4] Caminho mais rápido (Dijkstra)")
        print("  [5] Análises estruturais")
        print("  [6] Gerar visualizações")
        print("  [0] Sair")

        choice = input("\n  Opção: ").strip()

        if choice == "1":
            menu_info(graph)
        elif choice == "2":
            menu_search_stop(graph)
        elif choice == "3":
            menu_bfs(graph)
        elif choice == "4":
            menu_dijkstra(graph)
        elif choice == "5":
            menu_analysis(graph)
        elif choice == "6":
            menu_visualizacao(graph)
        elif choice == "0":
            print("\n  Encerrando. Até mais!\n")
            break
        else:
            print("  Opção inválida. Tente novamente.")


if __name__ == "__main__":
    main()