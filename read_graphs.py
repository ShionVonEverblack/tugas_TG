#!/usr/bin/python

import sys
import os
import re  # Import Regex untuk membersihkan nama file
import matplotlib.pyplot as plt
import networkx as nx
from collections import defaultdict, Counter

# --- FUNGSI MEMBACA FILE ---
def read_edges_with_ports_to_stats(edges_file,
                                   wload_to_graph=None,  wload_to_port_info=None,
                                   wload_to_directed_longevity=None):
    
    if wload_to_graph is None:  wload_to_graph = {}
    if wload_to_port_info is None: wload_to_port_info = {}
        
    directed_longevity = defaultdict(Counter)
    port_to_freq = Counter()

    filename_only = os.path.basename(edges_file)
    # Filter file metadata dan file sampah sistem
    if filename_only.startswith(('grouping', 'prefix', 'candidate', 'id_gt', '.')):
        return wload_to_graph, wload_to_port_info, wload_to_directed_longevity

    print(f"   -> Cek file: {filename_only} ...", end=" ")

    try:
        fopen = open(edges_file, mode='r', encoding='utf-8', errors='ignore')
    except Exception as e:
        print(f"[ERROR] {e}")
        return wload_to_graph, wload_to_port_info, wload_to_directed_longevity

    valid_lines_count = 0
    with fopen: 
        for line in fopen:
            if line.startswith('#'): continue
            parts = line.split()
            
            if len(parts) < 3: continue

            # Pastikan kolom 2 & 3 adalah angka (Node ID)
            if not (parts[1].isdigit() and parts[2].isdigit()):
                continue

            wload_id = parts[0]
            
            # --- FILTER TAMBAHAN: Hapus ID Graf yang aneh-aneh ---
            # Jika ID mengandung karakter non-printable atau terlalu panjang, skip
            if len(wload_id) > 15 or not re.match(r'^[A-Za-z0-9_\-]+$', wload_id):
                continue

            v1 = parts[1]
            v2 = parts[2]
            
            ports = []
            if len(parts) > 3:
                ports = parts[3].split(',')

            if wload_id not in wload_to_graph:
                wload_to_graph[ wload_id ] = defaultdict(Counter)
            
            stats = wload_to_port_info.get(wload_id, None)
            if stats is None:
                stats = defaultdict(set)
                wload_to_port_info[ wload_id ] = stats

            ports_added = False
            for port_tuple in ports:
                if 'p' not in port_tuple: continue 
                port_part = port_tuple.split('-')[0]
                if port_part == '': continue
                
                port_to_freq[port_part] += 1
                stats[port_part].add((v1, v2))
                ports_added = True
                directed_longevity[wload_id][(v1, v2, port_part)] = 1
                
            if ports_added:
                wload_to_graph[wload_id][v1][v2] += 1
                wload_to_graph[wload_id][v2][v1] += 1
                valid_lines_count += 1
    
    if valid_lines_count > 0:
        print(f"[OK] {valid_lines_count} edges.")
    else:
        print("[SKIP] Bukan data graf.")

    if wload_to_directed_longevity is None:
        wload_to_directed_longevity  = directed_longevity
    else:
        for wload, triples in directed_longevity.items():
            for trip in triples:
                wload_to_directed_longevity[wload][trip] += 1
    
    return wload_to_graph, wload_to_port_info, wload_to_directed_longevity

# --- FUNGSI SCAN FOLDER ---
def read_edges_with_ports_to_stats_multiple_files(path):
    wload_to_gr = {} 
    wload_to_stats = {} 
    wload_to_directed_longevity = defaultdict(Counter)
    
    print(f'\n# Memulai SCAN di folder: {path}')
    
    all_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(root, file)
            all_files.append(full_path)

    if not all_files:
        print("\n[!] Folder KOSONG atau path salah.\n")
        return {}, {}, {}
    
    print(f'# Menemukan total {len(all_files)} file. Memproses...')
    
    for fname in all_files:
        wload_to_gr, wload_to_stats, wload_to_directed_longevity = read_edges_with_ports_to_stats(
            fname, wload_to_gr, wload_to_stats, wload_to_directed_longevity)
        
    return wload_to_gr, wload_to_stats, wload_to_directed_longevity

# --- FUNGSI GAMBAR GRAF (VISUALISASI) ---
def visualize_graph(graph_id, edge_data, max_nodes=50):
    # --- PEMBERSIH NAMA FILE (ANTI ERROR) ---
    # Hanya izinkan huruf, angka, underscore, dan strip. Buang sisanya.
    clean_id = re.sub(r'[^\w\-_]', '', graph_id)
    if not clean_id:
        clean_id = "unknown_graph"
        
    print(f"   -> Menggambar graf {clean_id} (Top {max_nodes} nodes)...")
    
    G = nx.DiGraph()
    
    temp_edges = []
    for u, neighbors in edge_data.items():
        for v, weight in neighbors.items():
            temp_edges.append((u, v, weight))
            
    node_degrees = Counter()
    for u, v, w in temp_edges:
        node_degrees[u] += 1
        node_degrees[v] += 1
        
    top_nodes = [node for node, count in node_degrees.most_common(max_nodes)]
    
    for u, v, w in temp_edges:
        if u in top_nodes and v in top_nodes:
            G.add_edge(u, v, weight=w)
    
    if G.number_of_nodes() == 0:
        print("      [!] Graf kosong setelah difilter.")
        return

    pos = nx.spring_layout(G, seed=42, k=0.5)
    
    plt.figure(figsize=(10, 8))
    nx.draw_networkx_nodes(G, pos, node_size=500, node_color='skyblue', alpha=0.9)
    nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5, edge_color='gray', arrowstyle='->', arrowsize=15)
    nx.draw_networkx_labels(G, pos, font_size=10, font_family="sans-serif")
    
    plt.title(f"Visualisasi Graf: {graph_id} (Top {max_nodes} Nodes)", fontsize=15)
    plt.axis('off')
    
    output_filename = f"graf_{clean_id}.png"
    
    try:
        plt.savefig(output_filename, format="PNG", dpi=150)
        plt.close()
        print(f"      [BERHASIL] Gambar disimpan: {output_filename}")
    except OSError as e:
        print(f"      [GAGAL SIMPAN] {e}")
        plt.close()

# --- MAIN PROGRAM ---
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python read_graphs.py <folder_name>")
        sys.exit(1)
    
    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"[ERROR] Folder '{path}' tidak ditemukan!")
        sys.exit(1)

    graphs, stats, longev = read_edges_with_ports_to_stats_multiple_files(path)
    
    workloads = sorted(graphs.keys(), key=lambda k: len(graphs[k]), reverse=True)
    
    if not workloads:
        print("\n[!] Tidak ada graf yang ditemukan untuk digambar.")
    else:
        print('\n' + '='*60)
        print('MULAI PROSES VISUALISASI')
        print('='*60)
        
        for w in workloads:
            edge_data = graphs[w]
            visualize_graph(w, edge_data, max_nodes=50)
            
        print('\n[SELESAI] Cek folder tempat script ini berada untuk melihat hasilnya.')