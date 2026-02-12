#!/usr/bin/python

import sys
import os
import csv

def format_size(size_bytes):
    """Mengubah byte menjadi KB, MB, atau GB agar mudah dibaca."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.2f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.2f} MB"
    else:
        return f"{size_bytes/(1024**3):.2f} GB"

def analyze_representation(filepath):
    filename = os.path.basename(filepath)
    
    # --- FILTER (Hanya TXT, Skip GZ) ---
    if filename.endswith('.gz') or not filename.lower().endswith('.txt'):
        return None
    if filename.startswith(('grouping', 'prefix', 'candidate', 'id_gt', '.')):
        return None

    unique_nodes = set()
    edge_count = 0
    graph_id = "unknown"

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith('#'): continue
                parts = line.split()
                if len(parts) < 3: continue
                
                # Validasi angka
                if not (parts[1].isdigit() and parts[2].isdigit()):
                    continue

                if edge_count == 0:
                    graph_id = parts[0]

                u, v = parts[1], parts[2]
                
                # Kita asumsikan Directed Graph untuk representasi
                unique_nodes.add(u)
                unique_nodes.add(v)
                edge_count += 1

    except Exception as e:
        return None

    V = len(unique_nodes) # Jumlah Vertices (Simpul)
    E = edge_count        # Jumlah Edges (Sisi)

    if V == 0: return None

    # --- PERHITUNGAN ANALISIS ---
    
    # 1. Densitas (Density)
    # Rumus Directed: D = E / (V * (V - 1))
    max_possible_edges = V * (V - 1)
    if max_possible_edges == 0:
        density = 0
    else:
        density = E / max_possible_edges

    # 2. Estimasi Memori (Dalam Bytes)
    
    # A. Adjacency Matrix (Butuh V x V sel)
    # Asumsi: 1 sel = 1 byte (misal tipe data boolean/int8)
    # Jika pakai integer standar (4 byte), kalikan 4.
    mem_matrix = (V * V) * 1 

    # B. Adjacency List (Butuh V head + E node)
    # Asumsi: Pointer/ID butuh 8 byte (64-bit architecture)
    # Rumus kasar: (V * 8) + (E * 8)
    mem_list = (V * 8) + (E * 8)

    # 3. Keputusan (Recommendation)
    # Biasanya: Jika Density < 5% (0.05) atau V sangat besar, gunakan List.
    if density < 0.1: # Di bawah 10% dianggap Sparse (Jarang)
        rec = "Adjacency List"
        reason = "Sparse (Jarang)"
    elif V > 5000:
        rec = "Adjacency List"
        reason = "V Terlalu Besar"
    else:
        rec = "Adjacency Matrix"
        reason = "Dense (Padat)"

    return {
        'id': graph_id,
        'filename': filename,
        'V': V,
        'E': E,
        'density': density,
        'mem_matrix': mem_matrix,
        'mem_list': mem_list,
        'recommendation': rec,
        'reason': reason
    }

def main(path):
    print(f"\n{'='*100}")
    print(f"{'ANALISIS REPRESENTASI GRAF (MATRIX vs LIST)':^100}")
    print(f"{'='*100}")

    if not os.path.exists(path):
        print(f"[ERROR] Folder '{path}' tidak ditemukan.")
        return

    results = []
    print("Sedang menghitung estimasi memori...", end="\r")

    for root, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(root, file)
            data = analyze_representation(full_path)
            if data:
                print(f"   -> Analisa: {file} ...                     ", end="\r")
                results.append(data)

    results.sort(key=lambda x: x['filename'])

    if not results:
        print("\n[!] Tidak ada data graf (.txt) ditemukan.")
        return

    # --- TAMPILAN TABEL TERMINAL ---
    # Header
    print(f"\n\n{'File':<20} {'Nodes(V)':<10} {'Edges(E)':<10} {'Density':<10} {'Est. Matrix':<12} {'Est. List':<12} {'Saran':<15}")
    print("-" * 95)

    for res in results:
        d_perc = f"{res['density']*100:.2f}%"
        m_mat = format_size(res['mem_matrix'])
        m_list = format_size(res['mem_list'])
        
        print(f"{res['filename']:<20} {res['V']:<10} {res['E']:<10} {d_perc:<10} {m_mat:<12} {m_list:<12} {res['recommendation']:<15}")

    # --- SIMPAN KE CSV ---
    output_csv = "analisis_representasi.csv"
    try:
        with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Graph ID', 'Nama File', 'Nodes (V)', 'Edges (E)', 'Density', 'Est. Memori Matrix', 'Est. Memori List', 'Rekomendasi', 'Alasan'])
            
            for res in results:
                writer.writerow([
                    res['id'],
                    res['filename'],
                    res['V'],
                    res['E'],
                    f"{res['density']:.6f}",
                    format_size(res['mem_matrix']),
                    format_size(res['mem_list']),
                    res['recommendation'],
                    res['reason']
                ])
        print(f"\n{'='*100}")
        print(f"[INFO] Laporan lengkap disimpan di: {output_csv}")
        print("Buka file CSV untuk melihat alasan kenapa List/Matrix dipilih.")
        print(f"{'='*100}\n")
    except Exception as e:
        print(f"\n[ERROR] Gagal simpan CSV: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python analisa_representasi.py <folder_name>")
        sys.exit(1)
    
    path = sys.argv[1]
    main(path)