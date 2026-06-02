# 🚌 Análise de Rede de Transporte Público com Grafos

Trabalho Final — Teoria dos Grafos  
Modelagem e análise da rede de ônibus da **ETUFOR (Fortaleza-CE)** utilizando dados reais no formato **GTFS (General Transit Feed Specification)**.

---

## 📋 Sobre o Projeto

Este projeto transforma os dados públicos de transporte da ETUFOR em um **dígrafo ponderado** e aplica algoritmos clássicos de grafos para responder perguntas reais sobre a rede:

- Qual o caminho com **menos paradas** entre dois pontos?
- Qual o caminho **mais rápido**?
- Quais são as paradas mais **estratégicas** da rede?
- A rede é **conectada**? Existem paradas isoladas?
- Existem **ciclos** na rede?

---

## 🗂️ Estrutura do Projeto

```
projeto_grafos/
│
├── data/                        # Arquivos GTFS da ETUFOR (não versionados)
│   ├── stops.txt                # Paradas de ônibus (coordenadas e nomes)
│   ├── routes.txt               # Linhas comerciais
│   ├── trips.txt                # Viagens (execuções de cada linha)
│   └── stop_times.txt           # Sequência de paradas por viagem
│
├── src/                         # Código-fonte
│   ├── loader.py                # Leitura e parsing dos arquivos GTFS
│   ├── graph.py                 # Estrutura do grafo + construção
│   ├── algorithms.py            # BFS e Dijkstra implementados do zero
│   ├── analysis.py              # Análises estruturais da rede
│   ├── main.py                  # Menu interativo (ponto de entrada)
│   └── visualizacao.py          # Visualizações com NetworkX e Matplotlib
│
├── output/                      # Imagens geradas (criado automaticamente)
│   ├── 1_mapa_geografico.png
│   ├── 2_grafo_hubs.png
│   └── 3_bfs_vs_dijkstra.png
│
└── README.md
```

---

## 🧠 Modelagem Matemática

A rede de transporte é modelada como um **dígrafo ponderado** `G = (V, A, W)`:

| Elemento | Representa | Quantidade |
|---|---|---|
| **Vértice** | Uma parada de ônibus | 5.490 |
| **Aresta** | Conexão direta entre duas paradas consecutivas em uma linha | 18.679 |
| **Peso** | Tempo médio de viagem em minutos (ou distância em km como fallback) | — |

**Representação interna:** Lista de Adjacência  
**Deduplicação:** uma aresta por par `(linha, parada_A → parada_B)`, com peso sendo a média de todas as viagens observadas naquele trecho.

### Cálculo de Peso

1. **Prioridade:** diferença entre `departure_time` de A e `arrival_time` de B (em minutos)
2. **Fallback:** distância geográfica pela fórmula de Haversine (em km), usada quando os horários estão ausentes no arquivo

---

## 🔁 Fluxo do Sistema

```
arquivo_google.zip
       │
       ▼
   loader.py ──────────────────► GTFSData
       │                        (stops, trips, routes, stop_times)
       ▼
   graph.py ───────────────────► Graph
       │                        (vértices + lista de adjacência)
       │
       ├──► main.py (menu interativo)
       │         │
       │         ├──► algorithms.py  →  BFS / Dijkstra
       │         └──► analysis.py    →  algorithms.py
       │
       └──► visualizacao.py ──► NetworkX ──► PNG
```

Ao executar o `main.py`, o sistema:
1. Carrega os 4 arquivos GTFS via `loader.py`
2. Constrói o grafo em memória via `graph.py`
3. Mantém o grafo ativo durante toda a sessão do menu
4. Chama `algorithms.py` e `analysis.py` sob demanda conforme a opção escolhida

---

## ⚙️ Instalação

### Pré-requisitos

- Python 3.11 ou superior
- pip

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/projeto-grafos-etufor.git
cd projeto-grafos-etufor
```

### 2. Instale as dependências

```bash
pip install networkx matplotlib
```

> As demais bibliotecas usadas (`csv`, `math`, `heapq`, `collections`, `dataclasses`) fazem parte da biblioteca padrão do Python — nenhuma instalação adicional necessária.

### 3. Adicione os dados GTFS

Baixe o arquivo GTFS da ETUFOR e extraia o conteúdo na pasta `data/`:

```
data/
├── stops.txt
├── routes.txt
├── trips.txt
└── stop_times.txt
```

> ⚠️ Os arquivos de dados não estão versionados no repositório por conta do tamanho (~50 MB). O `stop_times.txt` possui mais de 1,1 milhão de linhas.

---

## ▶️ Como Executar

### Menu interativo (recomendado)

```bash
cd src
python main.py
```

```
=======================================================
  ANÁLISE DE REDE DE TRANSPORTE PÚBLICO — ETUFOR
  Trabalho Final — Teoria dos Grafos
=======================================================

  Carregando dados GTFS...

=======================================================
  MENU PRINCIPAL
=======================================================
  [1] Informações do grafo
  [2] Buscar parada por nome
  [3] Caminho com menos paradas (BFS)
  [4] Caminho mais rápido (Dijkstra)
  [5] Análises estruturais
  [0] Sair
```

**Dica:** use a opção `[2] Buscar parada por nome` para encontrar o ID de uma parada antes de usar as opções 3 e 4.

### Visualizações

```bash
cd src
python visualizacao.py
```

As imagens são salvas automaticamente na pasta `output/`.

---

## 📊 Algoritmos Implementados

### BFS — Busca em Largura

Percorre o grafo nível por nível a partir de uma origem. Garante o caminho com o **menor número de paradas**, sem considerar os pesos das arestas.

- **Complexidade:** `O(V + E)`
- **Uso no projeto:** caminho com menos conexões, análise de alcançabilidade, detecção de componentes conexos

### Dijkstra — Caminho Mínimo

Encontra o caminho de **menor custo acumulado** (tempo ou distância) entre dois vértices. Utiliza heap binário (`heapq`) para eficiência.

- **Complexidade:** `O((V + E) log V)`
- **Uso no projeto:** caminho mais rápido, comparativo com BFS

---

## 🔍 Análises Estruturais

| Análise | O que revela |
|---|---|
| **Grau dos vértices** | Quais paradas têm mais conexões de entrada e saída |
| **Conectividade** | Se a rede forma um único componente; paradas isoladas |
| **Detecção de ciclos** | Se existem rotas circulares (DFS com marcação de estados) |
| **Hubs** | As paradas mais estratégicas por grau total |
| **BFS vs Dijkstra** | Trade-off entre número de paradas e custo de viagem |

### Resultados sobre a rede da ETUFOR

- **97,1%** das paradas pertencem a um único componente conectado
- **160 paradas** isoladas (sem viagens ativas no período do dataset)
- Os **4 maiores hubs** são os terminais físicos: Siqueira, Papicu, Parangaba e José de Alencar
- O grafo **contém ciclos** — esperado em redes de transporte com ida e volta
- Dijkstra pode usar mais paradas intermediárias, mas chega a economizar **mais de 50% do custo** em relação ao BFS

---

## 🗺️ Visualizações

### 1. Mapa Geográfico da Rede Completa
Todas as paradas ativas plotadas nas coordenadas reais de Fortaleza. A intensidade da cor indica o grau do vértice; os terminais principais aparecem destacados em laranja.

### 2. Grafo dos Hubs
Subgrafo com as paradas de grau ≥ 10 (403 vértices) em layout spring. Permite visualizar a estrutura de conexão entre os pontos mais importantes da rede.

### 3. BFS vs Dijkstra
Comparativo visual entre os dois caminhos para o trajeto Terminal Siqueira → Terminal Papicu. Azul = BFS, vermelho = Dijkstra, cinza = trecho compartilhado.

---

## 📦 Dependências

| Biblioteca | Versão mínima | Uso |
|---|---|---|
| `networkx` | 3.0 | Conversão e visualização do grafo |
| `matplotlib` | 3.7 | Renderização dos gráficos |

Biblioteca padrão utilizada: `csv`, `math`, `heapq`, `collections`, `dataclasses`, `os`, `sys`

---

## 📁 Formato dos Dados (GTFS)

| Arquivo | Campos utilizados | Descrição |
|---|---|---|
| `stops.txt` | `stop_id`, `stop_name`, `stop_lat`, `stop_lon` | Paradas (vértices) |
| `routes.txt` | `route_id`, `route_short_name`, `route_long_name` | Linhas comerciais |
| `trips.txt` | `trip_id`, `route_id` | Viagens (instâncias de cada linha) |
| `stop_times.txt` | `trip_id`, `stop_id`, `stop_sequence`, `arrival_time`, `departure_time` | Sequência e horários |

---

## 👤 Autor

Desenvolvido como Trabalho Final (AV3) da disciplina de Teoria dos Grafos.  
Dados fornecidos pela **ETUFOR — Empresa de Transporte Urbano de Fortaleza**.