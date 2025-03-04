from itertools import permutations
import time

graf = {
    'A': ['B', 'C'],
    'B': ['A', 'D', 'E'],
    'C': ['A', 'F'],
    'D': ['B'],
    'E': ['B', 'F'],
    'F': ['C', 'E'],
    'G': ['H', 'J'],
    'H': ['G', 'I'],
    'I': ['H', 'J'],
    'J': ['G', 'I'],
    'K': ['L'],
    'L': ['K']
}

def cari_jalur(graf, awal, akhir, jalur=[]):
    jalur = jalur + [awal]
    if awal == akhir:
        return [jalur]
    if awal not in graf:
        return []
    semua_jalur = []
    for node in graf[awal]:
        if node not in jalur:
            jalur_baru = cari_jalur(graf, node, akhir, jalur)
            for j in jalur_baru:
                semua_jalur.append(j)
    return semua_jalur

def cari_semua_jalur(graf, awal, akhir, jalur=[]):
    jalur = jalur + [awal]
    if awal == akhir:
        return [jalur]
    if awal not in graf:
        return []
    semua_jalur = []
    for node in graf[awal]:
        if node not in jalur:
            jalur_baru = cari_semua_jalur(graf, node, akhir, jalur)
            for j in jalur_baru:
                semua_jalur.append(j)
    return semua_jalur

def cari_semua_siklus(graf, awal, jalur=[]):
    jalur = jalur + [awal]
    if len(jalur) > 1 and jalur[0] == jalur[-1]:
        return [jalur]
    if awal not in graf:
        return []
    semua_siklus = []
    for node in graf[awal]:
        if node not in jalur or (node == jalur[0] and len(jalur) > 2):
            siklus_baru = cari_semua_siklus(graf, node, jalur)
            for s in siklus_baru:
                semua_siklus.append(s)
    return semua_siklus

def cari_sirkuit_terpendek_terpanjang(graf, awal, akhir):
    semua_jalur = cari_semua_jalur(graf, awal, akhir)
    if not semua_jalur:
        return None, None
    terpendek = min(semua_jalur, key=len)
    terpanjang = max(semua_jalur, key=len)
    return terpendek, terpanjang

def tantangan_1():
    print("Tantangan 1:")
    mulai = time.time()
    print("1. Jalur dari A ke D:", cari_jalur(graf, 'A', 'D'))
    print("2. Semua kemungkinan jalur dari A ke D:", cari_semua_jalur(graf, 'A', 'D'))
    print("3. Semua kemungkinan siklus jika A adalah titik awal:", cari_semua_siklus(graf, 'A'))
    selesai = time.time()
    print(f"Waktu eksekusi: {selesai - mulai:.2f} detik")

def tantangan_2():
    print("Tantangan 2:")
    mulai = time.time()
    print("1. Semua kemungkinan jalur dari A ke C:", cari_semua_jalur(graf, 'A', 'C'))
    print("2. Semua kemungkinan siklus jika C adalah titik awal:", cari_semua_siklus(graf, 'C'))
    print("3. Semua kemungkinan siklus jika B adalah titik awal:", cari_semua_siklus(graf, 'B'))
    terpendek, terpanjang = cari_sirkuit_terpendek_terpanjang(graf, 'A', 'C')
    print("4. Sirkuit terpendek dan terpanjang dari A ke C:", terpendek, terpanjang)
    selesai = time.time()
    print(f"Waktu eksekusi: {selesai - mulai:.2f} detik")

def tantangan_3():
    print("Tantangan 3:")
    mulai = time.time()
    print("1. Semua kemungkinan jalur dari A ke K:", cari_semua_jalur(graf, 'A', 'K'))
    print("2. Semua kemungkinan jalur dari G ke J:", cari_semua_jalur(graf, 'G', 'J'))
    print("3. Semua kemungkinan jalur dari E ke F:", cari_semua_jalur(graf, 'E', 'F'))
    print("4. Semua kemungkinan siklus jika A adalah titik awal:", cari_semua_siklus(graf, 'A'))
    print("5. Semua kemungkinan siklus jika K adalah titik awal:", cari_semua_siklus(graf, 'K'))
    terpendek, terpanjang = cari_sirkuit_terpendek_terpanjang(graf, 'A', 'K')
    print("6. Sirkuit terpendek dan terpanjang dari A ke K:", terpendek, terpanjang)
    terpendek, terpanjang = cari_sirkuit_terpendek_terpanjang(graf, 'G', 'J')
    print("7. Sirkuit terpendek dan terpanjang dari G ke J:", terpendek, terpanjang)
    terpendek, terpanjang = cari_sirkuit_terpendek_terpanjang(graf, 'E', 'F')
    print("8. Sirkuit terpendek dan terpanjang dari E ke F:", terpendek, terpanjang)
    selesai = time.time()
    print(f"Waktu eksekusi: {selesai - mulai:.2f} detik")

def main():
    print("Pilih tantangan yang ingin diuji:")
    print("1. Tantangan 1")
    print("2. Tantangan 2")
    print("3. Tantangan 3")
    pilihan = input("Masukkan nomor tantangan: ")
    
    if pilihan == '1':
        tantangan_1()
    elif pilihan == '2':
        tantangan_2()
    elif pilihan == '3':
        tantangan_3()
    else:
        print("Pilihan tidak valid. Silakan pilih 1, 2, atau 3.")

if __name__ == "__main__":
    main()
