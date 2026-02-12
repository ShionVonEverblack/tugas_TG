#!/usr/bin/python

import sys
import os
import csv  # Library untuk membuat file CSV/Excel

def process_graph_file(filepath):
    """
    Membaca satu file dan menghitung set node unik serta total derajat.
    """
    unique_nodes = set()
    total_degree_sum = 0
    valid_edges = 0
    graph_id = "unknown"

    filename = os.path.basename(filepath)
    
    # --- FILTER BARU (MODIFIKASI) ---
    # 1. Abaikan file .gz agar tidak diekstrak/dibaca
    if filename.endswith('.gz'):
        return None

    # 2. HANYA proses jika akhiran file adalah .txt (Case insensitive, jadi .TXT juga terbaca)
    if not filename.lower().endswith('.txt'):
        return None

    # 3. Abaikan file metadata/sampah lainnya
    if filename.startswith(('grouping', 'prefix', 'candidate', 'id_gt', '.')):
        return None
    # --------------------------------

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith('#'): continue
                
                parts = line.split()
                
                # Syarat: Minimal 4 kolom (ID, Node1, Node2, PortInfo)
                if len(parts) < 4: continue
                
                # Pastikan Node ID berupa angka
                if not (parts[1].isdigit() and parts[2].isdigit()):
                    continue

                if valid_edges == 0:
                    graph_id = parts[0]

                u = parts[1]
                v = parts[2]
                port_info = parts[3]

                # Cek apakah ini edge valid (harus mengandung port 'p')
                if 'p' in port_info:
                    unique_nodes.add(u)
                    unique_nodes.add(v)
                    # Total Derajat = In + Out (setiap edge menambah 2 ke total sistem)
                    total_degree_sum += 2
                    valid_edges += 1

    except Exception as e:
        print(f"[ERROR] Gagal membaca {filename}: {e}")
        return None

    if valid_edges == 0:
        return None

    return {
        'id': graph_id,
        'filename': filename,
        'nodes': len(unique_nodes),
        'total_degree': total_degree_sum,
        'edges': valid_edges
    }

def main(path):
    print(f"\n# MEMULAI ANALISA GRAF (HANYA .TXT) DI FOLDER: {path}")
    print("-" * 60)

    if not os.path.exists(path):
        print(f"[ERROR] Folder '{path}' tidak ditemukan.")
        return

    # 1. Kumpulkan Data (Deep Scan)
    results = []
    for root, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(root, file)
            
            # Kita filter di dalam fungsi process_graph_file, 
            # tapi kita cek juga di sini untuk print log yang rapi
            if file.lower().endswith('.txt'):
                print(f"   -> Memproses: {file} ...", end="\r") 
                data = process_graph_file(full_path)
                if data:
                    results.append(data)

    # Urutkan hasil berdasarkan nama file
    results.sort(key=lambda x: x['filename'])

    if not results:
        print("\n[!] Tidak ada data graf (.txt) ditemukan.")
        return

    # 2. SIMPAN KE CSV (Excel)
    output_filename = "statistik_graf.csv"
    
    try:
        with open(output_filename, mode='w', newline='', encoding='utf-8') as csv_file:
            # Tentukan Header Kolom
            fieldnames = ['Graph ID', 'Nama File', 'Total Simpul (Nodes)', 'Total Derajat', 'Total Edge']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            writer.writeheader()
            
            # Tulis baris data
            for res in results:
                writer.writerow({
                    'Graph ID': res['id'],
                    'Nama File': res['filename'],
                    'Total Simpul (Nodes)': res['nodes'],
                    'Total Derajat': res['total_degree'],
                    'Total Edge': res['edges']
                })
                
        print(f"\n\n[BERHASIL] Data telah disimpan ke file: {output_filename}")
        print("Silakan buka file tersebut menggunakan Excel.\n")
        
    except PermissionError:
        print(f"\n[ERROR] Gagal menyimpan ke {output_filename}.")
        print("Pastikan file tersebut tidak sedang dibuka di Excel!")

    # 3. Tampilkan Preview Singkat di Terminal
    print("PREVIEW DATA:")
    print(f"{'Graph ID':<10} {'Nodes':<10} {'Degree':<10}")
    print("-" * 35)
    for res in results[:5]: # Hanya tampilkan 5 baris pertama
        print(f"{res['id']:<10} {res['nodes']:<10} {res['total_degree']:<10}")
    if len(results) > 5:
        print("... (sisanya lihat di CSV)")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python hitung_total_csv.py <folder_name>")
        sys.exit(1)
    
    path = sys.argv[1]
    main(path)