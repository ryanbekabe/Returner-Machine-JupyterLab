import sys
import math
import argparse
from collections import Counter
# permutasi_rank.py
# Menyimpan file sebagai (histogram byte + nomor urut permutasi / rank),
# lalu menyusun kembali file aslinya tanpa brute force (enumerative coding).

parser = argparse.ArgumentParser(description='Encode/decode data sebagai histogram byte + rank permutasi.')
grup = parser.add_mutually_exclusive_group(required=True)
grup.add_argument('namafile', nargs='?', help='file yang akan dianalisis')
grup.add_argument('--teks', help='gunakan teks ini (UTF-8) sebagai data')
args = parser.parse_args()

if args.teks is not None:
    data = args.teks.encode('utf-8')
else:
    try:
        with open(args.namafile, 'rb') as fd:
            data = fd.read()
    except OSError as e:
        sys.exit('Gagal membuka file: %s' % e)

n = len(data)
if n == 0:
    sys.exit('Data kosong.')
if n > 100000:
    print('Peringatan: data besar, perhitungan rank bisa lambat.')


def jumlah_permutasi(counts):
    # n! / (c1! * c2! * ...) : banyaknya susunan berbeda dengan histogram yang sama
    total = math.factorial(sum(counts.values()))
    for c in counts.values():
        total //= math.factorial(c)
    return total


def rank(data):
    # Nomor urut (mulai 0) data di antara semua permutasi histogramnya,
    # diurutkan secara leksikografis berdasarkan nilai byte 0..255
    counts = Counter(data)
    sisa = len(data)
    total = jumlah_permutasi(counts)
    r = 0
    for byte in data:
        # total = banyaknya susunan untuk posisi ini sampai akhir
        for b in sorted(counts):
            if b >= byte:
                break
            if counts[b] > 0:
                r += total * counts[b] // sisa
        total = total * counts[byte] // sisa
        counts[byte] -= 1
        sisa -= 1
    return r


def unrank(r, histogram):
    # Kebalikan rank(): susun kembali data dari histogram + rank
    counts = Counter(histogram)
    sisa = sum(counts.values())
    total = jumlah_permutasi(counts)
    hasil = bytearray()
    while sisa > 0:
        for b in sorted(counts):
            if counts[b] == 0:
                continue
            blok = total * counts[b] // sisa
            if r < blok:
                hasil.append(b)
                total = blok
                counts[b] -= 1
                sisa -= 1
                break
            r -= blok
    return bytes(hasil)


def tampil(bs):
    return bs.decode('utf-8', errors='replace') if all(32 <= b < 127 for b in bs) else bs.hex()


histogram = Counter(data)
total = jumlah_permutasi(histogram)
r = rank(data)
hasil = unrank(r, histogram)

print('Data                  :', tampil(data))
print('Ukuran                :', n, 'byte =', n * 8, 'bit')
print('Histogram             :', ', '.join('%s=%d' % (tampil(bytes([b])), c) for b, c in sorted(histogram.items())))
print()

# Efek "tanda" posisi: berapa kandidat tersisa jika k byte awal + k byte akhir diketahui
print('Kandidat permutasi tersisa jika posisi tertentu ditandai:')
print('%-34s %20s' % ('Tanda', 'Kandidat'))
maks_k = n // 2
for k in range(0, min(maks_k, 4) + 1):
    tengah = Counter(data[k:n - k])
    if k == 0:
        label = 'tanpa tanda'
    else:
        label = 'awal "%s" + akhir "%s"' % (tampil(data[:k]), tampil(data[n - k:]))
    print('%-34s %20d' % (label, jumlah_permutasi(tengah)))
print()

bit_rank = max(1, math.ceil(math.log2(total)))
entropy = -sum(c / n * math.log2(c / n) for c in histogram.values()) + 0.0  # hindari -0.0
print('Total permutasi        :', total)
print('Rank (nomor urut)      :', r)
print('Bit untuk rank         :', bit_rank, 'bit')
print('Batas Shannon n*H      : %.2f bit' % (n * entropy))
print()

if hasil == data:
    print('Decode dari histogram + rank:', tampil(hasil), '-> SAMA PERSIS dengan data asli')
else:
    sys.exit('Decode GAGAL: %s' % tampil(hasil))
