import sys
import math
import time
import zlib
import lzma
import argparse
from collections import Counter
# rmh.py - Return[er] Machine Hash (enumerative coding)
# Menyimpan file sebagai histogram byte + rank permutasi ke file .rmh,
# lalu menyusun kembali file aslinya dari file .rmh tersebut.
#
# Format file .rmh (semua angka "varint" = LEB128 tanpa tanda):
#   [4 byte ] magic "RMH1"
#   [varint ] n          : ukuran file asli (byte)
#   [varint ] k          : jumlah nilai byte berbeda
#   k kali:
#     [1 byte ] nilai byte (0..255, urut naik)
#     [varint ] frekuensi
#   [4 byte ] CRC32 file asli (untuk verifikasi)
#   [m byte ] rank, big-endian. m tidak disimpan: dihitung dari histogram,
#             m = jumlah byte untuk menampung (total_permutasi - 1)

MAGIC = b'RMH1'


# ---------- varint (LEB128) ----------

def tulis_varint(angka):
    hasil = bytearray()
    while True:
        b = angka & 0x7F
        angka >>= 7
        if angka:
            hasil.append(b | 0x80)
        else:
            hasil.append(b)
            return bytes(hasil)


def baca_varint(data, pos):
    angka = 0
    geser = 0
    while True:
        if pos >= len(data):
            raise ValueError('File .rmh terpotong (varint tidak lengkap)')
        b = data[pos]
        pos += 1
        angka |= (b & 0x7F) << geser
        if not b & 0x80:
            return angka, pos
        geser += 7


# ---------- enumerative coding ----------

def jumlah_permutasi(histogram):
    # n! / (c1! * c2! * ...)
    total = math.factorial(sum(histogram.values()))
    for c in histogram.values():
        total //= math.factorial(c)
    return total


def panjang_rank(total):
    # jumlah byte untuk menyimpan rank terbesar (total - 1)
    return ((total - 1).bit_length() + 7) // 8


def rank(data, histogram):
    # Sama seperti permutasi_rank.py, tetapi jumlah susunan untuk semua byte
    # yang lebih kecil dihitung sekaligus: total * (jumlah frekuensi byte < x) / sisa
    counts = dict(histogram)
    simbol = sorted(counts)
    sisa = len(data)
    total = jumlah_permutasi(histogram)
    r = 0
    for byte in data:
        lebih_kecil = 0
        for b in simbol:
            if b >= byte:
                break
            lebih_kecil += counts[b]
        if lebih_kecil:
            r += total * lebih_kecil // sisa
        total = total * counts[byte] // sisa
        counts[byte] -= 1
        sisa -= 1
    return r


def unrank(r, histogram):
    counts = dict(histogram)
    simbol = sorted(counts)
    sisa = sum(counts.values())
    total = jumlah_permutasi(histogram)
    hasil = bytearray()
    while sisa > 0:
        # cari byte b terkecil dengan r < total * (frekuensi kumulatif s/d b) / sisa
        t = r * sisa // total
        kumulatif = 0
        for b in simbol:
            c = counts[b]
            if c == 0:
                continue
            if t < kumulatif + c:
                break
            kumulatif += c
        if kumulatif:
            r -= total * kumulatif // sisa
        hasil.append(b)
        total = total * c // sisa
        counts[b] -= 1
        sisa -= 1
    return bytes(hasil)


# ---------- format file .rmh ----------

def encode(data):
    histogram = Counter(data)
    total = jumlah_permutasi(histogram) if data else 1
    r = rank(data, histogram) if data else 0

    header = MAGIC + tulis_varint(len(data)) + tulis_varint(len(histogram))
    bagian_histogram = b''.join(bytes([b]) + tulis_varint(c) for b, c in sorted(histogram.items()))
    crc = zlib.crc32(data).to_bytes(4, 'big')
    bagian_rank = r.to_bytes(panjang_rank(total), 'big')

    rincian = {
        'header': len(header),
        'histogram': len(bagian_histogram),
        'crc32': len(crc),
        'rank': len(bagian_rank),
    }
    return header + bagian_histogram + crc + bagian_rank, rincian


def baca_rmh(isi):
    # Mengurai file .rmh menjadi (n, histogram, crc, rank)
    if isi[:4] != MAGIC:
        raise ValueError('Bukan file .rmh (magic tidak cocok)')
    pos = 4
    n, pos = baca_varint(isi, pos)
    k, pos = baca_varint(isi, pos)
    if k > 256:
        raise ValueError('Jumlah nilai byte berbeda tidak valid: %d' % k)
    histogram = {}
    for _ in range(k):
        if pos >= len(isi):
            raise ValueError('File .rmh terpotong (histogram tidak lengkap)')
        b = isi[pos]
        c, pos = baca_varint(isi, pos + 1)
        histogram[b] = c
    if sum(histogram.values()) != n:
        raise ValueError('Jumlah frekuensi histogram tidak sama dengan ukuran file')
    crc = int.from_bytes(isi[pos:pos + 4], 'big')
    pos += 4
    total = jumlah_permutasi(histogram) if n else 1
    m = panjang_rank(total)
    if len(isi) - pos != m:
        raise ValueError('Panjang rank tidak sesuai (diharapkan %d byte, ada %d)' % (m, len(isi) - pos))
    r = int.from_bytes(isi[pos:], 'big')
    if r >= total:
        raise ValueError('Rank melebihi jumlah permutasi')
    return n, histogram, crc, r, total


def decode(isi):
    n, histogram, crc, r, total = baca_rmh(isi)
    data = unrank(r, histogram) if n else b''
    if zlib.crc32(data) != crc:
        raise ValueError('CRC32 tidak cocok, hasil decode rusak')
    return data


# ---------- perintah ----------

def baca_file(nama):
    try:
        with open(nama, 'rb') as fd:
            return fd.read()
    except OSError as e:
        sys.exit('Gagal membuka file: %s' % e)


def tulis_file(nama, isi):
    try:
        with open(nama, 'wb') as fd:
            fd.write(isi)
    except OSError as e:
        sys.exit('Gagal menulis file: %s' % e)


def persen(a, b):
    return '%.1f%%' % (a / b * 100) if b else '-'


def cmd_encode(args):
    data = baca_file(args.input)
    output = args.output or args.input + '.rmh'
    if len(data) > 20000:
        print('Peringatan: file %d byte, proses bisa lambat (kompleksitas kuadratik).' % len(data))

    mulai = time.perf_counter()
    isi, rincian = encode(data)
    durasi = time.perf_counter() - mulai
    tulis_file(output, isi)

    n = len(data)
    print('Encode  :', args.input, '->', output, '(%.3f detik)' % durasi)
    print()
    print('Rincian file .rmh:')
    for nama, ukuran in rincian.items():
        print('  %-10s %10d byte' % (nama, ukuran))
    print('  %-10s %10d byte' % ('TOTAL', len(isi)))
    print()
    print('Perbandingan ukuran:')
    print('  %-12s %10d byte' % ('asli', n))
    print('  %-12s %10d byte  (%s dari asli)' % ('.rmh', len(isi), persen(len(isi), n)))
    z = len(zlib.compress(data, 9))
    x = len(lzma.compress(data, preset=9))
    print('  %-12s %10d byte  (%s dari asli)' % ('zlib -9', z, persen(z, n)))
    print('  %-12s %10d byte  (%s dari asli)' % ('lzma -9', x, persen(x, n)))
    if n:
        h = -sum(c / n * math.log2(c / n) for c in Counter(data).values()) + 0.0
        print('  %-12s %10.1f byte  (batas Shannon orde-0, n*H/8)' % ('n*H/8', n * h / 8))


def cmd_decode(args):
    isi = baca_file(args.input)
    if args.output:
        output = args.output
    elif args.input.endswith('.rmh'):
        output = args.input[:-4] + '.decoded'
    else:
        output = args.input + '.decoded'

    mulai = time.perf_counter()
    try:
        data = decode(isi)
    except ValueError as e:
        sys.exit('Decode gagal: %s' % e)
    durasi = time.perf_counter() - mulai
    tulis_file(output, data)
    print('Decode  :', args.input, '->', output, '(%.3f detik)' % durasi)
    print('Ukuran  :', len(data), 'byte, CRC32 cocok')


def cmd_info(args):
    isi = baca_file(args.input)
    try:
        n, histogram, crc, r, total = baca_rmh(isi)
    except ValueError as e:
        sys.exit('File tidak valid: %s' % e)
    print('File .rmh        :', args.input, '(%d byte)' % len(isi))
    print('Ukuran file asli :', n, 'byte')
    print('Nilai byte unik  :', len(histogram))
    print('CRC32            : %08X' % crc)
    print('Total permutasi  : %d digit' % len(str(total)) if total > 10 ** 30 else 'Total permutasi  : %d' % total)
    print('Rank             : %d digit' % len(str(r)) if r > 10 ** 30 else 'Rank             : %d' % r)
    print('Histogram        :')
    for b, c in sorted(histogram.items()):
        char = chr(b) if 32 <= b < 127 else '.'
        print('  %3d (0x%02X) %s : %d' % (b, b, char, c))


def main():
    parser = argparse.ArgumentParser(description='Return[er] Machine Hash: simpan file sebagai histogram + rank (.rmh).')
    sub = parser.add_subparsers(dest='perintah', required=True)

    p = sub.add_parser('encode', help='file asli -> file .rmh')
    p.add_argument('input')
    p.add_argument('-o', '--output', help='nama file .rmh (default: <input>.rmh)')
    p.set_defaults(func=cmd_encode)

    p = sub.add_parser('decode', help='file .rmh -> file asli')
    p.add_argument('input')
    p.add_argument('-o', '--output', help='nama file hasil (default: <input tanpa .rmh>.decoded)')
    p.set_defaults(func=cmd_decode)

    p = sub.add_parser('info', help='tampilkan isi file .rmh')
    p.add_argument('input')
    p.set_defaults(func=cmd_info)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
