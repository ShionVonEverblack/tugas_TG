#!/usr/bin/python

import sys
import os
import csv
from collections import Counter

def get_node_degrees(filepath):
    """
    Membaca file dan mengembalikan Counter object berisi derajat setiap node.
    """
    filename = os.path.basename(filepath)
    
    # --- FILTER (Hanya TXT, Skip GZ) ---
    # PERBAIKAN: Semua return harus mengembalikan DUA nilai (None, None)
    if filename.endswith('.gz'): 
        return None, None
    
    if not filename.lower().endswith('.txt'): 
        return None, None  # <-- Dulu error disini karena cuma return None
    
    if filename.startswith(('grouping', 'prefix', 'candidate', 'id_gt', '.')): 
        return None, None  # <-- Dulu error disini

    degrees = Counter()
    graph_id = "unknown"
    valid_lines = 0

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith('#'): continue
                parts = line.split()
                
                if len(parts) < 4: continue
                if not (parts[1].isdigit() and parts[2].isdigit()): continue

                if valid_lines == 0:
                    graph_id = parts[0]

                u, v = parts[1], parts[2]
                port_info = parts[3]

                # Validasi edge dengan port
                if 'p' in port_info:
                    # Degree = In + Out (Undirected view for total connectivity)
                    degrees[u] += 1
                    degrees[v] += 1
                    valid_lines += 1

    except Exception as e:
        print(f"[ERROR] {filename}: {e}")
        return None, None

    if valid_lines == 0: return None, None
    
    return graph_id, degrees

def save_distribution_csv(graph_id, sorted_nodes):
    """Menyimpan seluruh distribusi ke CSV"""
    if not graph_id: graph_id = "unknown"
    filename = f"distribusi_{graph_id}.csv"
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Rank', 'Node ID', 'Degree'])
            for rank, (node, deg) in enumerate(sorted_nodes, 1):
                writer.writerow([rank, node, deg])
        return filename
    except:
        return None

def main(path):
    print(f"\n{'='*80}")
    print(f"{'DISTRIBUSI DERAJAT (TOP 50 & BOTTOM 50)':^80}")
    print(f"{'='*80}")

    if not os.path.exists(path):
        print(f"[ERROR] Folder '{path}' tidak ditemukan.")
        return

    # Scan Folder
    for root, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(root, file)
            
            # Proses File (Sekarang aman karena selalu return tuple)
            g_id, degrees = get_node_degrees(full_path)
            
            if degrees:
                print(f"\n>>> HASIL ANALISIS FILE: {file} (ID: {g_id})")
                print("-" * 60)
                
                # Urutkan: Terbesar ke Terkecil
                sorted_nodes = degrees.most_common()
                total_nodes = len(sorted_nodes)

                # --- BAGIAN 1: TOP 50 (TERBESAR) ---
                print(f"A. 50 SIMPUL DERAJAT TERBESAR (Paling Sibuk)")
                print(f"{'Rank':<5} {'Node ID':<15} {'Degree':<10} {'|':<3} {'Rank':<5} {'Node ID':<15} {'Degree':<10}")
                print("-" * 75)
                
                top_50 = sorted_nodes[:50]
                
                # Tampilan 2 Kolom agar hemat tempat
                half = (len(top_50) + 1) // 2
                for i in range(half):
                    # Kolom Kiri
                    r1 = i + 1
                    n1, d1 = top_50[i]
                    col1 = f"{r1:<5} {n1:<15} {d1:<10}"
                    
                    # Kolom Kanan
                    col2 = ""
                    if i + half < len(top_50):
                        r2 = i + half + 1
                        n2, d2 = top_50[i+half]
                        col2 = f"|  {r2:<5} {n2:<15} {d2:<10}"
                    
                    print(f"{col1} {col2}")

                print("\n")

                # --- BAGIAN 2: BOTTOM 50 (TERKECIL) ---
                print(f"B. 50 SIMPUL DERAJAT TERKECIL (Paling Sepi)")
                print(f"(Biasanya node user biasa/client)")
                print("-" * 75)
                
                # Ambil 50 terbawah (slice dari belakang)
                bottom_50 = sorted_nodes[-50:]
                # Balik urutan agar yang paling kecil (1) muncul duluan
                bottom_50.reverse() 
                
                # Print baris per baris
                limit = 0
                for node, deg in bottom_50:
                    if limit % 5 == 0 and limit != 0: print() # Enter setiap 5 item
                    print(f"[{node}: {deg}]", end="  ")
                    limit += 1
                print("\n")

                # --- BAGIAN 3: SIMPAN CSV ---
                saved_file = save_distribution_csv(g_id, sorted_nodes)
                if saved_file:
                    print(f"[INFO] Data lengkap {total_nodes} node disimpan ke: {saved_file}")
                
                print("="*80)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python distribusi_derajat.py <folder_name>")
        sys.exit(1)
    
    path = sys.argv[1]
    main(path)