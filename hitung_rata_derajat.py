#!/usr/bin/python

import sys
import os
import csv

def calculate_avg_degree(filepath):
    """
    Membaca file, menghitung node dan edge, lalu mencari rata-rata derajat.
    Hanya membaca file .txt dan MENGABAIKAN .gz
    """
    unique_nodes = set()
    edge_count = 0
    graph_id = "unknown"
    
    filename = os.path.basename(filepath)
    
    # --- FILTER FILE (PENTING) ---
    # 1. Jangan sentuh file GZ
    if filename.endswith('.gz'):
        return None
        
    # 2. Hanya proses file TXT (Case insensitive)
    if not filename.lower().endswith('.txt'):
        return None

    # 3. Filter file metadata/sampah sistem
    if filename.startswith(('grouping', 'prefix', 'candidate', 'id_gt', '.')):
        return None
    # -----------------------------

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith('#'): continue
                
                parts = line.split()
                
                # Format: ID Node1 Node2 PortInfo
                if len(parts) < 4: continue
                
                # Validasi angka (ID Node harus angka)
                if not (parts[1].isdigit() and parts[2].isdigit()):
                    continue

                if edge_count == 0:
                    graph_id = parts[0]

                u, v = parts[1], parts[2]
                port_info = parts[3]

                # Hitung hanya jika ada informasi port (koneksi valid dengan 'p')
                if 'p' in port_info:
                    unique_nodes.add(u)
                    unique_nodes.add(v)
                    edge_count += 1

    except Exception as e:
        # Jika error baca file, abaikan saja
        return None

    num_nodes = len(unique_nodes)
    
    # Hindari pembagian dengan nol jika file kosong
    if num_nodes == 0:
        return None

    # RUMUS: Avg Degree = (2 * Edges) / Nodes
    avg_degree = (edge_count * 2) / num_nodes

    return {
        'id': graph_id,
        'filename': filename,
        'nodes': num_nodes,
        'edges': edge_count,
        'avg_degree': avg_degree
    }

def main(path):
    print(f"\n{'='*80}")
    print(f"{'MENGHITUNG DERAJAT RATA-RATA (HANYA FILE .TXT)':^80}")
    print(f"{'='*80}")

    if not os.path.exists(path):
        print(f"[ERROR] Folder '{path}' tidak ditemukan.")
        return

    results = []
    
    # Deep Scan (Menelusuri semua sub-folder)
    print("Sedang memproses data...", end="\r")
    
    for root, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(root, file)
            
            # Kita panggil fungsi, dia akan otomatis return None jika itu .gz
            data = calculate_avg_degree(full_path)
            
            if data:
                # Tampilkan progres real-time hanya untuk file yang valid
                print(f"   -> Memproses: {file} ...           ", end="\r")
                results.append(data)

    # Urutkan berdasarkan nama file
    results.sort(key=lambda x: x['filename'])

    if not results:
        print("\n[!] Tidak ada data graf (.txt) ditemukan.")
        return

    # 1. TAMPILKAN DI TERMINAL
    print(f"\n\n{'Graph ID':<15} {'Nodes':<10} {'Edges':<10} {'Avg Degree':<15}")
    print("-" * 55)
    
    for res in results:
        # Format angka desimal 2 digit
        print(f"{res['id']:<15} {res['nodes']:<10} {res['edges']:<10} {res['avg_degree']:.2f}")

    # 2. SIMPAN KE CSV
    output_csv = "rata_rata_derajat.csv"
    try:
        with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Header Excel
            writer.writerow(['Graph ID', 'Nama File', 'Jumlah Node', 'Jumlah Edge', 'Rata-rata Derajat'])
            
            for res in results:
                writer.writerow([
                    res['id'], 
                    res['filename'], 
                    res['nodes'], 
                    res['edges'], 
                    round(res['avg_degree'], 4) # 4 angka belakang koma
                ])
        
        print(f"{'='*80}")
        print(f"[SUKSES] Data lengkap disimpan di file: {output_csv}")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"\n[ERROR] Gagal menyimpan CSV: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python hitung_rata_derajat.py <folder_name>")
        sys.exit(1)
    
    path = sys.argv[1]
    main(path)