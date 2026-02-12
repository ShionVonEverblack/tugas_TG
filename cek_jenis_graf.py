    #!/usr/bin/python

import sys
import os
import csv

def determine_graph_type(filepath):
    """
    Menganalisa file .txt untuk menentukan karakteristik graf:
    1. Apakah memiliki Self-Loops? (u -> u)
    2. Apakah Multigraph? (Multiple edges antara u -> v)
    """
    filename = os.path.basename(filepath)
    
    # --- FILTER KETAT (Hanya TXT, Skip GZ) ---
    if filename.endswith('.gz'):
        return None
    if not filename.lower().endswith('.txt'):
        return None
    if filename.startswith(('grouping', 'prefix', 'candidate', 'id_gt', '.')):
        return None
    # -----------------------------------------

    edge_set = set()       # Untuk mendeteksi duplikat (Multigraph)
    has_self_loop = False
    is_multigraph = False
    valid_lines = 0
    graph_id = "unknown"

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith('#'): continue
                parts = line.split()
                
                # Format minimal: ID u v ...
                if len(parts) < 3: continue
                
                # Pastikan u dan v adalah angka
                if not (parts[1].isdigit() and parts[2].isdigit()):
                    continue

                if valid_lines == 0:
                    graph_id = parts[0]

                u = parts[1]
                v = parts[2]
                
                # Cek Self Loop (Simpul mengarah ke diri sendiri)
                if u == v:
                    has_self_loop = True

                # Cek Multigraph (Apakah edge u->v sudah pernah ada?)
                # Kita anggap ini Directed (Berarah) karena data jaringan
                edge_pair = (u, v)
                
                if edge_pair in edge_set:
                    is_multigraph = True
                else:
                    edge_set.add(edge_pair)
                
                valid_lines += 1

    except Exception as e:
        print(f"[ERROR] {filename}: {e}")
        return None

    if valid_lines == 0:
        return None

    # --- MENENTUKAN KESIMPULAN JENIS GRAF ---
    # Asumsi dasar: Data jaringan biasanya Directed (Berarah)
    properties = []
    
    if is_multigraph:
        base_type = "Directed Multigraph"
    else:
        base_type = "Directed Simple Graph"
        
    if has_self_loop:
        properties.append("with Loops")
    
    final_type = base_type + " " + " ".join(properties)

    return {
        'id': graph_id,
        'filename': filename,
        'has_loops': "Ya" if has_self_loop else "Tidak",
        'is_multigraph': "Ya" if is_multigraph else "Tidak",
        'type_conclusion': final_type.strip()
    }

def main(path):
    print(f"\n{'='*90}")
    print(f"{'ANALISA JENIS GRAF (HANYA TXT)':^90}")
    print(f"{'='*90}")

    if not os.path.exists(path):
        print(f"[ERROR] Folder '{path}' tidak ditemukan.")
        return

    results = []
    
    print("Sedang menganalisa struktur graf...", end="\r")
    
    # Deep Scan Folder
    for root, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(root, file)
            
            # Proses file
            data = determine_graph_type(full_path)
            
            if data:
                print(f"   -> Cek: {file} ...                   ", end="\r")
                results.append(data)

    # Urutkan berdasarkan nama file
    results.sort(key=lambda x: x['filename'])

    if not results:
        print("\n[!] Tidak ada file graf (.txt) yang valid.")
        return

    # 1. TAMPILKAN DI TERMINAL
    print(f"\n\n{'Graph ID':<15} {'Self-Loop?':<12} {'Multigraph?':<12} {'Kesimpulan Jenis':<30}")
    print("-" * 80)
    
    for res in results:
        print(f"{res['id']:<15} {res['has_loops']:<12} {res['is_multigraph']:<12} {res['type_conclusion']:<30}")

    # 2. SIMPAN KE CSV
    output_csv = "jenis_graf.csv"
    try:
        with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['Graph ID', 'Nama File', 'Ada Self-Loop', 'Apakah Multigraph', 'Jenis Graf'])
            writer.writeheader()
            
            for res in results:
                writer.writerow({
                    'Graph ID': res['id'],
                    'Nama File': res['filename'],
                    'Ada Self-Loop': res['has_loops'],
                    'Apakah Multigraph': res['is_multigraph'],
                    'Jenis Graf': res['type_conclusion']
                })
        
        print(f"\n{'='*90}")
        print(f"[SUKSES] Laporan jenis graf disimpan di: {output_csv}")
        print(f"{'='*90}\n")
        
    except Exception as e:
        print(f"\n[ERROR] Gagal menyimpan CSV: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python cek_jenis_graf.py <folder_name>")
        sys.exit(1)
    
    path = sys.argv[1]
    main(path)