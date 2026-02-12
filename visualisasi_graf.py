#!/usr/bin/python

print("--- [DEBUG] Script mulai berjalan... ---")

import sys
import os

# 1. CEK LIBRARY DULU
try:
    import networkx as nx
    import matplotlib
    # PENTING: Gunakan backend 'Agg' agar tidak error di terminal/server
    matplotlib.use('Agg') 
    import matplotlib.pyplot as plt
    print("--- [DEBUG] Library berhasil dimuat ---")
except ImportError as e:
    print(f"\n[ERROR FATAL] Library belum lengkap: {e}")
    print("Silakan jalankan perintah ini di terminal:")
    print("pip install networkx matplotlib scipy")
    sys.exit(1)

def visualize_sample(filepath, limit_nodes=50):
    filename = os.path.basename(filepath)
    
    # Filter File
    if filename.endswith('.gz') or not filename.lower().endswith('.txt'):
        return
    if filename.startswith(('grouping', 'prefix', 'candidate', 'id_gt', '.')):
        return

    print(f"   -> Membaca: {filename} ...")

    G = nx.DiGraph()
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith('#'): continue
                parts = line.split()
                if len(parts) < 3: continue
                if not (parts[1].isdigit() and parts[2].isdigit()): continue

                u, v = parts[1], parts[2]
                G.add_edge(u, v)
                
                # Batas sampling (agar tidak berat)
                if G.number_of_nodes() >= limit_nodes:
                    break
    except Exception as e:
        print(f"[SKIP] Error baca file {filename}: {e}")
        return

    if G.number_of_nodes() == 0:
        return

    print(f"      [PROSES] Menggambar graf ({G.number_of_nodes()} nodes)...")

    # --- PLOTTING ---
    plt.figure(figsize=(10, 10))
    
    # Layout (Posisi node)
    try:
        pos = nx.spring_layout(G, k=0.5, seed=42)
    except:
        # Fallback jika scipy tidak ada
        pos = nx.random_layout(G)

    # Derajat node untuk ukuran
    d = dict(G.degree)
    node_sizes = [v * 50 + 100 for v in d.values()] 

    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color='#87CEFA', alpha=0.9)
    nx.draw_networkx_edges(G, pos, edge_color='gray', alpha=0.5, arrows=True)
    nx.draw_networkx_labels(G, pos, font_size=8)

    plt.title(f"Sample Graph: {filename}", fontsize=12)
    plt.axis('off')

    # Simpan Gambar
    output_img = f"visualisasi_{filename}.png"
    plt.savefig(output_img, dpi=150)
    plt.close() # Bersihkan memori
    
    print(f"      [SUKSES] Disimpan ke: {output_img}")

def main(path):
    print(f"\n{'='*60}")
    print(f"{'VISUALISASI GRAF (DEBUG MODE)':^60}")
    print(f"{'='*60}")

    if not os.path.exists(path):
        print(f"[ERROR] Folder '{path}' tidak ditemukan.")
        return

    found = False
    for root, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(root, file)
            # Cek ekstensi manual sebelum masuk fungsi agar user tahu
            if file.endswith('.txt') and not file.startswith('.'):
                found = True
                visualize_sample(full_path, limit_nodes=50)

    if not found:
        print("[INFO] Tidak ditemukan file .txt di folder tersebut.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python visualisasi_graf.py <folder_name>")
        sys.exit(1)
    
    path = sys.argv[1]
    main(path)