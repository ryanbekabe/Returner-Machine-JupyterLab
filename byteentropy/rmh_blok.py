import os
import sys
import math
import time
import zlib
import lzma
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

import rmh
# rmh_blok.py - Return[er] Machine Hash per blok
# Lanjutan rmh.py: file dipecah menjadi blok-blok berukuran tetap, setiap blok
# disimpan sebagai histogram + rank sendiri. Waktu proses menjadi linear
# terhadap ukuran file, dan blok bisa diproses paralel di beberapa core CPU.
#
# Format file .rmb (varint = LEB128, sama seperti rmh.py):
#   [4 byte ] magic "RMB1"
#   [varint ] n          : ukuran file asli (byte)
#   [varint ] B          : ukuran blok (byte); blok terakhir boleh lebih pendek
#   [4 byte ] CRC32 seluruh file asli
#   untuk setiap blok (jumlah blok = ceil(n / B), tidak disimpan):
#     [varint ] k        : jumlah nilai byte berbeda di blok ini
#     k kali: [1 byte] nilai byte + [varint] frekuensi
#     [m byte ] rank blok, big-endian (m dihitung dari histogram blok)

MAGIC = b'RMB1'
UKURAN_BLOK_DEFAULT = 4096


# ---------- satu blok ----------

def encode_blok(data):
    # blok -> (bytes histogram, bytes rank)
    histogram = Counter(data)
    total = rmh.jumlah_permutasi(histogram)
    r = rmh.rank(data, histogram)
    bagian_histogram = rmh.tulis_varint(len(histogram)) + b''.join(
        bytes([b]) + rmh.tulis_varint(c) for b, c in sorted(histogram.items()))
    return bagian_histogram, r.to_bytes(rmh.panjang_rank(total), 'big')


def decode_blok(tugas):
    r, histogram = tugas
    return rmh.unrank(r, histogram)


def bagi_blok(data, ukuran_blok):
    return [data[i:i + ukuran_blok] for i in range(0, len(data), ukuran_blok)]


def jalankan(fungsi, daftar, jobs):
    # jobs = 1 -> berurutan; jobs > 1 -> paralel di beberapa proses
    if jobs <= 1 or len(daftar) <= 1:
        return [fungsi(x) for x in daftar]
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        return list(pool.map(fungsi, daftar, chunksize=max(1, len(daftar) // (jobs * 4))))


# ---------- format file .rmb ----------

def encode(data, ukuran_blok, jobs=1):
    if ukuran_blok < 1:
        raise ValueError('Ukuran blok minimal 1 byte')
    hasil_blok = jalankan(encode_blok, bagi_blok(data, ukuran_blok), jobs)

    header = MAGIC + rmh.tulis_varint(len(data)) + rmh.tulis_varint(ukuran_blok)
    crc = zlib.crc32(data).to_bytes(4, 'big')
    isi = bytearray(header + crc)
    rincian = {'header': len(header), 'crc32': len(crc), 'histogram': 0, 'rank': 0}
    for bagian_histogram, bagian_rank in hasil_blok:
        isi += bagian_histogram + bagian_rank
        rincian['histogram'] += len(bagian_histogram)
        rincian['rank'] += len(bagian_rank)
    return bytes(isi), rincian, len(hasil_blok)


def baca_rmb(isi):
    # Mengurai file .rmb menjadi (n, ukuran_blok, crc, [(rank, histogram), ...])
    if isi[:4] != MAGIC:
        raise ValueError('Bukan file .rmb (magic tidak cocok)')
    pos = 4
    n, pos = rmh.baca_varint(isi, pos)
    ukuran_blok, pos = rmh.baca_varint(isi, pos)
    if ukuran_blok < 1:
        raise ValueError('Ukuran blok tidak valid')
    if pos + 4 > len(isi):
        raise ValueError('File .rmb terpotong (CRC32 tidak lengkap)')
    crc = int.from_bytes(isi[pos:pos + 4], 'big')
    pos += 4

    blok = []
    sisa = n
    while sisa > 0:
        panjang = min(ukuran_blok, sisa)
        k, pos = rmh.baca_varint(isi, pos)
        if not 1 <= k <= 256:
            raise ValueError('Blok %d: jumlah nilai byte berbeda tidak valid (%d)' % (len(blok), k))
        histogram = {}
        for _ in range(k):
            if pos >= len(isi):
                raise ValueError('File .rmb terpotong (histogram blok %d)' % len(blok))
            b = isi[pos]
            c, pos = rmh.baca_varint(isi, pos + 1)
            histogram[b] = c
        if sum(histogram.values()) != panjang:
            raise ValueError('Blok %d: jumlah frekuensi tidak sama dengan panjang blok' % len(blok))
        total = rmh.jumlah_permutasi(histogram)
        m = rmh.panjang_rank(total)
        if pos + m > len(isi):
            raise ValueError('File .rmb terpotong (rank blok %d)' % len(blok))
        r = int.from_bytes(isi[pos:pos + m], 'big')
        pos += m
        if r >= total:
            raise ValueError('Blok %d: rank melebihi jumlah permutasi' % len(blok))
        blok.append((r, histogram))
        sisa -= panjang
    if pos != len(isi):
        raise ValueError('Ada %d byte sisa di akhir file .rmb' % (len(isi) - pos))
    return n, ukuran_blok, crc, blok


def decode(isi, jobs=1):
    n, ukuran_blok, crc, blok = baca_rmb(isi)
    data = b''.join(jalankan(decode_blok, blok, jobs))
    if zlib.crc32(data) != crc:
        raise ValueError('CRC32 tidak cocok, hasil decode rusak')
    return data


# ---------- perintah ----------

def cmd_encode(args):
    data = rmh.baca_file(args.input)
    output = args.output or args.input + '.rmb'
    mulai = time.perf_counter()
    try:
        isi, rincian, jumlah_blok = encode(data, args.blok, args.jobs)
    except ValueError as e:
        sys.exit('Encode gagal: %s' % e)
    durasi = time.perf_counter() - mulai
    rmh.tulis_file(output, isi)

    n = len(data)
    print('Encode  :', args.input, '->', output, '(%.3f detik, %d blok x %d byte, %d proses)'
          % (durasi, jumlah_blok, args.blok, args.jobs))
    print()
    print('Rincian file .rmb:')
    for nama, ukuran in rincian.items():
        print('  %-10s %10d byte' % (nama, ukuran))
    print('  %-10s %10d byte' % ('TOTAL', len(isi)))
    print()
    print('Perbandingan ukuran:')
    print('  %-12s %10d byte' % ('asli', n))
    print('  %-12s %10d byte  (%s dari asli)' % ('.rmb', len(isi), rmh.persen(len(isi), n)))
    z = len(zlib.compress(data, 9))
    x = len(lzma.compress(data, preset=9))
    print('  %-12s %10d byte  (%s dari asli)' % ('zlib -9', z, rmh.persen(z, n)))
    print('  %-12s %10d byte  (%s dari asli)' % ('lzma -9', x, rmh.persen(x, n)))


def cmd_decode(args):
    isi = rmh.baca_file(args.input)
    if args.output:
        output = args.output
    elif args.input.endswith('.rmb'):
        output = args.input[:-4] + '.decoded'
    else:
        output = args.input + '.decoded'
    mulai = time.perf_counter()
    try:
        data = decode(isi, args.jobs)
    except ValueError as e:
        sys.exit('Decode gagal: %s' % e)
    durasi = time.perf_counter() - mulai
    rmh.tulis_file(output, data)
    print('Decode  :', args.input, '->', output, '(%.3f detik, %d proses)' % (durasi, args.jobs))
    print('Ukuran  :', len(data), 'byte, CRC32 cocok')


def cmd_info(args):
    isi = rmh.baca_file(args.input)
    try:
        n, ukuran_blok, crc, blok = baca_rmb(isi)
    except ValueError as e:
        sys.exit('File tidak valid: %s' % e)
    print('File .rmb        :', args.input, '(%d byte)' % len(isi))
    print('Ukuran file asli :', n, 'byte')
    print('Ukuran blok      :', ukuran_blok, 'byte')
    print('Jumlah blok      :', len(blok))
    print('CRC32            : %08X' % crc)
    print()
    print('%6s %8s %8s %12s %10s' % ('Blok', 'Panjang', 'Byte unik', 'Rank (byte)', 'Entropy'))
    if args.semua or len(blok) <= 20:
        nomor_tampil = list(range(len(blok)))
    else:
        nomor_tampil = list(range(10)) + [None] + list(range(len(blok) - 5, len(blok)))
    for nomor in nomor_tampil:
        if nomor is None:
            print('%6s' % '...')
            continue
        r, histogram = blok[nomor]
        panjang = sum(histogram.values())
        h = -sum(c / panjang * math.log2(c / panjang) for c in histogram.values()) + 0.0
        print('%6d %8d %8d %12d %10.4f' % (nomor, panjang, len(histogram),
                                         rmh.panjang_rank(rmh.jumlah_permutasi(histogram)), h))


def cmd_analisis(args):
    # Coba beberapa ukuran blok untuk melihat tarik-ulur ukuran file vs kecepatan
    data = rmh.baca_file(args.input)
    n = len(data)
    print('File:', args.input, '(%d byte), %d proses' % (n, args.jobs))
    print()
    print('%10s %8s %12s %12s %12s %10s %10s' % ('Blok', 'Jumlah', 'Histogram', 'Rank', 'Total .rmb', '% asli', 'Detik'))
    for ukuran_blok in args.ukuran:
        mulai = time.perf_counter()
        isi, rincian, jumlah_blok = encode(data, ukuran_blok, args.jobs)
        durasi = time.perf_counter() - mulai
        print('%10d %8d %12d %12d %12d %9s %10.3f' % (ukuran_blok, jumlah_blok, rincian['histogram'],
                                                     rincian['rank'], len(isi), rmh.persen(len(isi), n), durasi))
    print()
    print('%10s %8s %12s %12s %12d %9s' % ('zlib -9', '', '', '', len(zlib.compress(data, 9)),
                                           rmh.persen(len(zlib.compress(data, 9)), n)))
    print('%10s %8s %12s %12s %12d %9s' % ('lzma -9', '', '', '', len(lzma.compress(data, preset=9)),
                                           rmh.persen(len(lzma.compress(data, preset=9)), n)))


def main():
    parser = argparse.ArgumentParser(description='Return[er] Machine Hash per blok: histogram + rank untuk setiap blok (.rmb).')
    sub = parser.add_subparsers(dest='perintah', required=True)
    jobs_default = os.cpu_count() or 1

    p = sub.add_parser('encode', help='file asli -> file .rmb')
    p.add_argument('input')
    p.add_argument('-o', '--output', help='nama file .rmb (default: <input>.rmb)')
    p.add_argument('-b', '--blok', type=int, default=UKURAN_BLOK_DEFAULT,
                   help='ukuran blok dalam byte (default: %d)' % UKURAN_BLOK_DEFAULT)
    p.add_argument('-j', '--jobs', type=int, default=jobs_default,
                   help='jumlah proses paralel (default: jumlah core = %d)' % jobs_default)
    p.set_defaults(func=cmd_encode)

    p = sub.add_parser('decode', help='file .rmb -> file asli')
    p.add_argument('input')
    p.add_argument('-o', '--output', help='nama file hasil (default: <input tanpa .rmb>.decoded)')
    p.add_argument('-j', '--jobs', type=int, default=jobs_default,
                   help='jumlah proses paralel (default: %d)' % jobs_default)
    p.set_defaults(func=cmd_decode)

    p = sub.add_parser('info', help='tampilkan isi file .rmb per blok')
    p.add_argument('input')
    p.add_argument('--semua', action='store_true', help='tampilkan semua blok')
    p.set_defaults(func=cmd_info)

    p = sub.add_parser('analisis', help='bandingkan beberapa ukuran blok (tanpa menulis file)')
    p.add_argument('input')
    p.add_argument('-u', '--ukuran', type=int, nargs='+', default=[256, 1024, 4096, 16384],
                   help='daftar ukuran blok yang dicoba (default: 256 1024 4096 16384)')
    p.add_argument('-j', '--jobs', type=int, default=jobs_default,
                   help='jumlah proses paralel (default: %d)' % jobs_default)
    p.set_defaults(func=cmd_analisis)

    args = parser.parse_args()
    if getattr(args, 'jobs', 1) < 1:
        sys.exit('Jumlah proses (-j) minimal 1')
    args.func(args)


if __name__ == '__main__':
    main()
