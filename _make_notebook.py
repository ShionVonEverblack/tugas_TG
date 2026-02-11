import json


def md_cell(text):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": text.splitlines(keepends=True),
    }


def code_cell(code):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": code.splitlines(keepends=True),
    }

cells = []

cells.append(md_cell(
"""# Eksplorasi Graf Cisco_22_networks (IPYNB)

Notebook ini mengikuti poin tugas 4(a) sampai 4(h):
1. hitung jumlah simpul dan sisi
2. hitung derajat rata-rata
3. tentukan jenis graf
4. analisis representasi (adjacency list / adjacency matrix)
5. distribusi derajat + 50 terbesar/terkecil
6. visualisasi sampel simpul
7. diskusi karakteristik struktural
8. eksplorasi tambahan
"""
))

cells.append(code_cell(
"""import gzip
import re
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

plt.style.use('seaborn-v0_8-whitegrid')
pd.set_option('display.max_rows', 60)
pd.set_option('display.max_columns', 20)
"""
))

cells.append(code_cell(
"""# =========================
# Konfigurasi utama
# =========================
DATA_SOURCE = Path('dir_g21_small_workload_with_gt/dir_no_packets_etc/edges_12hrs_feb10_all_49sensors.csv.txt')
# Contoh lain:
# DATA_SOURCE = Path('dir_20_graphs')
# DATA_SOURCE = Path('dir_g22_extra_graph_with_gt/dir_edges')

MAX_FILES = None         # batasi jumlah file jika source adalah folder
SELECT_GRAPH_ID = None   # None -> otomatis pilih graph id dengan edge terbanyak
TOP_K = 50
SAMPLE_NODES_VIS = 80
ADJ_MATRIX_NODES = 20
RANDOM_SEED = 7
"""
))

cells.append(code_cell(
"""def edge_files_from_path(path: Path, max_files=None):
    # Ambil file edge .txt/.gz. Jika .txt dan .txt.gz sama-sama ada, prioritaskan .gz.
    if path.is_file():
        return [path]

    all_files = [p for p in path.rglob('*') if p.is_file() and (p.suffix == '.gz' or p.suffix == '.txt')]
    if not all_files:
        raise FileNotFoundError(f'Tidak ada file .txt/.gz di {path}')

    chosen = {}
    for p in sorted(all_files):
        key = str(p.with_suffix('')) if p.suffix == '.gz' else str(p)
        if p.suffix == '.gz':
            chosen[key] = p
        elif key not in chosen:
            chosen[key] = p

    files = sorted(chosen.values())
    if max_files is not None:
        files = files[:max_files]
    return files


def open_maybe_gz(path: Path):
    if path.suffix == '.gz':
        return gzip.open(path, mode='rt', encoding='utf-8', errors='ignore')
    return open(path, mode='r', encoding='utf-8', errors='ignore')


def parse_ports(raw):
    # Parse token seperti: 1p6-22,1p17-4 -> [(1,6,22), (1,17,4)]
    out = []
    if raw is None:
        return out
    for token in str(raw).split(','):
        token = token.strip()
        if not token:
            continue
        m = re.match(r'^(\\d+)p(\\d+)(?:-(\\d+))?$', token)
        if not m:
            continue
        port = int(m.group(1))
        proto = int(m.group(2))
        packets = int(m.group(3)) if m.group(3) else 0
        out.append((port, proto, packets))
    return out


def load_edges(path: Path, max_files=None):
    files = edge_files_from_path(path, max_files=max_files)
    pair_records = []
    port_records = []

    for f in files:
        with open_maybe_gz(f) as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split()
                if len(parts) < 3:
                    continue

                graph_id = parts[0]
                src = str(parts[1])
                dst = str(parts[2])
                port_blob = parts[3] if len(parts) >= 4 else None

                pair_records.append((graph_id, src, dst, str(f)))

                for port, proto, packets in parse_ports(port_blob):
                    port_records.append((graph_id, src, dst, port, proto, packets, str(f)))

    if not pair_records:
        raise ValueError('Tidak ada edge valid yang terbaca.')

    df_pair = pd.DataFrame(pair_records, columns=['graph_id', 'src', 'dst', 'file'])
    df_port = pd.DataFrame(port_records, columns=['graph_id', 'src', 'dst', 'port', 'protocol', 'packets', 'file'])
    return files, df_pair, df_port


def choose_graph_id(df_pair, selected=None):
    if selected is not None:
        return selected
    return df_pair['graph_id'].value_counts().index[0]


def build_graphs(df_pair, graph_id):
    d = df_pair[df_pair['graph_id'] == graph_id][['src', 'dst']].copy()

    # DiGraph: edge unik terarah (u,v)
    dg = nx.DiGraph()
    for u, v in d.itertuples(index=False):
        if dg.has_edge(u, v):
            dg[u][v]['weight'] += 1
        else:
            dg.add_edge(u, v, weight=1)

    ug = nx.Graph()
    for u, v in d.itertuples(index=False):
        if ug.has_edge(u, v):
            ug[u][v]['weight'] += 1
        else:
            ug.add_edge(u, v, weight=1)

    return d, dg, ug
"""
))

cells.append(code_cell(
"""files, df_pair, df_port = load_edges(DATA_SOURCE, max_files=MAX_FILES)
active_graph_id = choose_graph_id(df_pair, SELECT_GRAPH_ID)
df_selected, Gd, Gu = build_graphs(df_pair, active_graph_id)

print(f'Jumlah file dibaca: {len(files)}')
print(f'Graph ID aktif: {active_graph_id}')
print('Graph ID tersedia (top 10):')
print(df_pair['graph_id'].value_counts().head(10))
"""
))

cells.append(md_cell("""## 4(a), 4(b), 4(c): Jumlah simpul/sisi, derajat rata-rata, dan jenis graf"""))

cells.append(code_cell(
"""num_nodes = Gu.number_of_nodes()
num_edges_undirected = Gu.number_of_edges()
num_edges_directed = Gd.number_of_edges()
num_self_loops = nx.number_of_selfloops(Gd)

avg_degree_undirected = (2 * num_edges_undirected / num_nodes) if num_nodes else 0.0
avg_in_degree = np.mean([d for _, d in Gd.in_degree()]) if num_nodes else 0.0
avg_out_degree = np.mean([d for _, d in Gd.out_degree()]) if num_nodes else 0.0

density_undirected = nx.density(Gu) if num_nodes > 1 else 0.0
density_directed = nx.density(Gd) if num_nodes > 1 else 0.0

node_set = set(Gd.nodes())
has_reciprocal_pairs = any(Gd.has_edge(v, u) for u, v in Gd.edges() if u != v)

print('=== Ringkasan Dasar ===')
print(f'Nodes: {num_nodes}')
print(f'Undirected edges (unik): {num_edges_undirected}')
print(f'Directed edges (unik): {num_edges_directed}')
print(f'Self-loops: {num_self_loops}')
print(f'Rata-rata derajat (undirected): {avg_degree_undirected:.4f}')
print(f'Rata-rata in-degree: {avg_in_degree:.4f}')
print(f'Rata-rata out-degree: {avg_out_degree:.4f}')
print(f'Density undirected: {density_undirected:.6f}')
print(f'Density directed: {density_directed:.6f}')

print('\\n=== Jenis Graf ===')
print(f'- Berarah: Ya (DiGraph)')
print(f'- Dapat diproyeksikan ke tak-berarah: Ya (Graph)')
print(f'- Berbobot: Ya, atribut weight menyimpan frekuensi kemunculan edge')
print(f'- Ada self-loop: {num_self_loops > 0}')
print(f'- Ada pasangan timbal balik (u->v dan v->u): {has_reciprocal_pairs}')
"""
))

cells.append(md_cell("""## 4(d): Representasi graf (adjacency list / adjacency matrix)"""))

cells.append(code_cell(
"""# Adjacency list (contoh 10 simpul pertama)
first_nodes = sorted(Gu.nodes())[:10]
adj_list_preview = {n: sorted(list(Gu.neighbors(n)))[:20] for n in first_nodes}

print('Adjacency list (preview):')
for n, neigh in adj_list_preview.items():
    print(f'{n}: {neigh}')

# Adjacency matrix (subset simpul agar tetap terbaca)
matrix_nodes = sorted(Gu.nodes())[:ADJ_MATRIX_NODES]
adj_matrix = nx.to_pandas_adjacency(Gu, nodelist=matrix_nodes, dtype=int)

print(f'\\nAdjacency matrix subset {len(matrix_nodes)} simpul pertama:')
display(adj_matrix)
"""
))

cells.append(md_cell("""## 4(e): Distribusi derajat simpul + 50 terbesar/terkecil"""))

cells.append(code_cell(
"""deg_und = pd.Series(dict(Gu.degree()), name='degree_undirected').sort_values(ascending=False)
deg_in = pd.Series(dict(Gd.in_degree()), name='in_degree').sort_values(ascending=False)
deg_out = pd.Series(dict(Gd.out_degree()), name='out_degree').sort_values(ascending=False)

print('Top-50 degree terbesar (undirected):')
display(deg_und.head(TOP_K).to_frame())

print('Top-50 degree terkecil (undirected):')
display(deg_und.sort_values(ascending=True).head(TOP_K).to_frame())

fig, ax = plt.subplots(1, 2, figsize=(12, 4))
ax[0].hist(deg_und.values, bins=30, color='#1f77b4', edgecolor='white')
ax[0].set_title('Histogram Degree (Undirected)')
ax[0].set_xlabel('Degree')
ax[0].set_ylabel('Frekuensi')

# skala log membantu melihat tail distribusi
ax[1].hist(deg_und.values, bins=30, color='#ff7f0e', edgecolor='white', log=True)
ax[1].set_title('Histogram Degree (Log Count)')
ax[1].set_xlabel('Degree')
ax[1].set_ylabel('Frekuensi (log)')

plt.tight_layout()
plt.show()
"""
))

cells.append(md_cell("""## 4(f): Visualisasi graf dari sampel simpul (50-100 simpul)"""))

cells.append(code_cell(
"""sample_nodes = sorted(Gu.nodes())[:SAMPLE_NODES_VIS]
Gs = Gu.subgraph(sample_nodes).copy()

plt.figure(figsize=(10, 8))
pos = nx.spring_layout(Gs, seed=RANDOM_SEED, k=0.45)
node_sizes = [30 + 20 * Gs.degree(n) for n in Gs.nodes()]

nx.draw_networkx_nodes(Gs, pos, node_size=node_sizes, node_color='#2a9d8f', alpha=0.85)
nx.draw_networkx_edges(Gs, pos, alpha=0.35, width=0.8)

if Gs.number_of_nodes() <= 60:
    nx.draw_networkx_labels(Gs, pos, font_size=7)

plt.title(f'Visualisasi Sampel {Gs.number_of_nodes()} Simpul ({active_graph_id})')
plt.axis('off')
plt.show()
"""
))

cells.append(md_cell("""## 4(g): Diskusi karakteristik struktural graf"""))

cells.append(code_cell(
"""components = list(nx.connected_components(Gu))
components_sorted = sorted(components, key=len, reverse=True)
num_components = len(components_sorted)
largest_cc_size = len(components_sorted[0]) if components_sorted else 0

clustering_avg = nx.average_clustering(Gu) if num_nodes > 1 else 0.0

print('Poin diskusi struktural (otomatis):')
print(f'1. Graf terdiri dari {num_components} komponen terhubung; komponen terbesar berisi {largest_cc_size} simpul.')
print(f'2. Rata-rata derajat undirected = {avg_degree_undirected:.3f}, menunjukkan kepadatan relasi per simpul.')
print(f'3. Clustering coefficient rata-rata = {clustering_avg:.4f}, indikasi kecenderungan triadic closure.')
print(f'4. Jumlah self-loop = {num_self_loops}, perlu ditafsirkan sebagai komunikasi internal node-ke-node sendiri.')
print(f'5. Adanya reciprocal pair = {has_reciprocal_pairs}, menandakan komunikasi dua arah antar pasangan simpul.')
"""
))

cells.append(md_cell("""## 4(h): Eksplorasi tambahan"""))

cells.append(code_cell(
"""# Eksplorasi tambahan 1: komponen terbesar + metrik jarak
if Gu.number_of_nodes() > 0:
    giant_nodes = max(nx.connected_components(Gu), key=len)
    G_giant = Gu.subgraph(giant_nodes).copy()

    print(f'Largest connected component: {G_giant.number_of_nodes()} nodes, {G_giant.number_of_edges()} edges')

    if G_giant.number_of_nodes() > 1:
        try:
            approx_diam = nx.diameter(G_giant)
            print(f'Diameter komponen terbesar: {approx_diam}')
        except Exception as e:
            print(f'Diameter tidak dihitung penuh (alasan: {e})')

# Eksplorasi tambahan 2: centrality (top-10 degree centrality)
centrality = nx.degree_centrality(Gu)
cent_top = pd.Series(centrality).sort_values(ascending=False).head(10)
print('\\nTop-10 degree centrality:')
display(cent_top.to_frame('degree_centrality'))

# Eksplorasi tambahan 3: port/protocol paling sering
if not df_port.empty:
    print('Top-10 kombinasi port-protocol:')
    port_proto_top = (
        df_port.groupby(['port', 'protocol'])
        .size()
        .sort_values(ascending=False)
        .head(10)
        .rename('freq')
        .reset_index()
    )
    display(port_proto_top)
else:
    print('Tidak ada data port/protocol ter-parse pada source ini.')
"""
))

cells.append(md_cell(
"""## Catatan Laporan

Untuk laporan akhir, gunakan output angka dan plot di atas lalu ringkas:
- kondisi ukuran graf (besar/kecil, sparse/dense),
- pola distribusi derajat (apakah heavy-tail),
- dominasi komponen terbesar,
- simpul paling sentral,
- pola service port/protocol yang menonjol.
"""
))

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.13",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

with open('graph_exploration.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=2)

print('created graph_exploration.ipynb')
