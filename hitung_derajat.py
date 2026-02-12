#!/usr/bin/python

import sys
import os
import re
import csv
from collections import defaultdict, Counter

# --- FUNGSI MEMBACA FILE (Sama seperti sebelumnya) ---
def read_graph_data(edges_file):
    # Dictionary untuk menyimpan derajat
    in_degree = Counter()   # Jumlah koneksi MASUK
    out_degree = Counter()  # Jumlah koneksi KELUAR
    nodes = set()           # Himpunan nama simpul unik
    
    filename_only = os.path.basename(edges_file)
    
    # Filter file metadata
    if filename_only.startswith(('grouping', 'prefix', 'candidate', 'id_gt', '.')):
        return None, None, None, None

    print(f"   -> Memproses: {filename_only} ...", end=" ")

    try:
        fopen = open(edges_file, mode='r', encoding='utf-8', errors='ignore')
    except Exception as e:
        print(f"[ERROR] {e}")
        return None, None, None, None

    valid_lines = 0
    graph_id = "unknown"

    with fopen: 
        for line in fopen:
            if line.startswith('#'): continue
            parts = line.split()
            
            if len(parts) < 3: continue

            # Validasi format angka
            if not (parts[1].isdigit() and parts[2].isdigit()):
                continue

            # Ambil ID Graf dari baris pertama yang valid
            if valid_lines == 0:
                graph_id = parts[0]
                # Bersihkan ID dari karakter aneh
                graph_id = re.sub(r'[^\w\-_]', '', graph_id)

            v1 = parts[1] # Source Node
            v2 = parts[2] # Target Node
            
            # Cek Port (Wajib ada 'p')
            has_port = False
            if len(parts) > 3:
                ports = parts[3].split(',')
                for p in ports:
                    if 'p' in p:
                        has_port = True
                        break
            
            if has_port:
                # Update Statistik
                nodes.add(v1)
                nodes.add(v2)
                out_degree[v1] += 1
                in_degree[v2] += 1
                valid_lines += 1
    
    if valid_lines > 0:
        print(f"[OK] ID: {graph_id} | {valid_lines} edges.")
        return graph_id, nodes, in_degree, out_degree
    else:
        print("[SKIP] Kosong/Bukan Graf.")
        return None, None, None, None

# --- FUNGSI UTAMA ---
def main(path):
    print(f'\n# MENGHITUNG DERAJAT DAN SIMPUL DI FOLDER: {path}')
    print('='*80)
    
    # Cari semua file
    all_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            all_files.append(os.path.join(root, file))

    if not all_files:
        print("[!] Tidak ada file ditemukan.")
        return

    # Header Tabel Laporan
    print(f"{'Graph ID':<15} {'Jml Simpul':<15} {'Jml Edge':<15} {'Max Degree':<15} {'Avg Degree':<15}")
    print('-'*80)

    for fname in all_files:
        g_id, nodes, in_deg, out_deg = read_graph_data(fname)
        
        if g_id:
            num_nodes = len(nodes)
            
            # Hitung Total Degree (In + Out) per node
            total_degree = Counter()
            for n in nodes:
                total_degree[n] = in_deg[n] + out_deg[n]
            
            # Statistik Sederhana
            total_edges = sum(out_deg.values())
            max_deg = max(total_degree.values()) if total_degree else 0
            avg_deg = (total_edges * 2) / num_nodes if num_nodes > 0 else 0
            
            # Print Baris Tabel
            print(f"{g_id:<15} {num_nodes:<15} {total_edges:<15} {max_deg:<15} {avg_deg:<15.2f}")
            
            # --- SIMPAN DETAIL KE CSV (Opsional) ---
            # Ini akan membuat file excel berisi derajat setiap node
            output_csv = f"stats_{g_id}.csv"
            try:
                with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['Node_ID', 'In_Degree', 'Out_Degree', 'Total_Degree']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    # Urutkan berdasarkan degree tertinggi
                    sorted_nodes = sorted(nodes, key=lambda n: total_degree[n], reverse=True)
                    
                    for n in sorted_nodes:
                        writer.writerow({
                            'Node_ID': n,
                            'In_Degree': in_deg[n],
                            'Out_Degree': out_deg[n],
                            'Total_Degree': total_degree[n]
                        })
                # Uncomment baris bawah jika ingin notifikasi file dibuat
                # print(f"   (Detail disimpan ke {output_csv})")
            except Exception as e:
                print(f"   [Gagal simpan CSV]: {e}")

    print('='*80)
    print("Selesai. File 'stats_*.csv' berisi detail setiap node telah dibuat.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python hitung_derajat.py <folder_name>")
        sys.exit(1)
    
    path = sys.argv[1]
    if os.path.exists(path):
        main(path)
    else:
        print(f"[ERROR] Folder {path} tidak ditemukan.")