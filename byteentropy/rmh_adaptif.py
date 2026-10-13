import sys
import time
import zlib
import lzma
import argparse

import rmh
# rmh_adaptif.py - Return[er] Machine Hash dengan histogram adaptif
# Lanjutan rmh_blok.py: histogram TIDAK disimpan di file. Histogram dipelajari
# dari byte-byte yang sudah terbuka; encoder dan decoder belajar dengan cara
# yang persis sama, sehingga tebakannya selalu identik.
#
# Rank dihitung bertahap per byte (arithmetic coding): setiap byte mempersempit
# interval [low, high] sebesar peluangnya menurut histogram saat itu. Bilangan
# di dalam interval akhir itulah "rank" seluruh file.
#
# Format file .rma (varint = LEB128):
#   [4 byte ] magic "RMA1"
#   [varint ] n          : ukuran file asli (byte)
#   [varint ] tambah     : penambahan frekuensi setiap byte muncul
#   [varint ] batas      : total frekuensi maksimum sebelum semua dibagi dua
#   [4 byte ] CRC32 file asli
#   [sisa   ] bit hasil arithmetic coding

MAGIC = b'RMA1'
TAMBAH_DEFAULT = 32
BATAS_DEFAULT = 1 << 16

# arithmetic coder 32-bit (Witten, Neal & Cleary 1987)
BIT = 32
PENUH = (1 << BIT) - 1
SETENGAH = 1 << (BIT - 1)
SEPEREMPAT = 1 << (BIT - 2)
TIGA_PEREMPAT = 3 * SEPEREMPAT


# ---------- model: histogram adaptif ----------

class Model:
    # Histogram 256 nilai byte, disimpan dalam Fenwick tree agar frekuensi
    # kumulatif bisa dihitung dalam 8 langkah (log2 256), bukan 256 langkah.
    def __init__(self, tambah, batas):
        self.tambah = tambah
        self.batas = batas
        self.frek = [1] * 256         # semua byte mulai dari 1: belum ada yang mustahil
        self.bangun_ulang()

    def bangun_ulang(self):
        self.pohon = [0] * 257
        for i, f in enumerate(self.frek):
            j = i + 1
            while j <= 256:
                self.pohon[j] += f
                j += j & -j
        self.total = sum(self.frek)

    def kumulatif(self, b):
        # jumlah frekuensi byte 0..b-1
        s = 0
        while b > 0:
            s += self.pohon[b]
            b -= b & -b
        return s

    def cari(self, target):
        # byte b dengan kumulatif(b) <= target < kumulatif(b + 1)
        pos = 0
        langkah = 256
        while langkah:
            berikut = pos + langkah
            if berikut <= 256 and self.pohon[berikut] <= target:
                pos = berikut
                target -= self.pohon[berikut]
            langkah >>= 1
        return pos

    def perbarui(self, b):
        self.frek[b] += self.tambah
        j = b + 1
        while j <= 256:
            self.pohon[j] += self.tambah
            j += j & -j
        self.total += self.tambah
        if self.total > self.batas:
            # bagi dua: data lama semakin dilupakan, data baru lebih dipercaya
            self.frek = [(f + 1) // 2 for f in self.frek]
            self.bangun_ulang()


# ---------- encode / decode ----------

def kode_aritmetika(data, tambah, batas):
    model = Model(tambah, batas)
    low, high, tertunda = 0, PENUH, 0
    bit_keluar = []

    def keluarkan(bit):
        nonlocal tertunda
        bit_keluar.append(bit)
        bit_keluar.extend([1 - bit] * tertunda)
        tertunda = 0

    for b in data:
        cum_low = model.kumulatif(b)
        cum_high = cum_low + model.frek[b]
        rentang = high - low + 1
        high = low + rentang * cum_high // model.total - 1
        low = low + rentang * cum_low // model.total
        while True:
            if high < SETENGAH:
                keluarkan(0)
            elif low >= SETENGAH:
                keluarkan(1)
                low -= SETENGAH
                high -= SETENGAH
            elif low >= SEPEREMPAT and high < TIGA_PEREMPAT:
                tertunda += 1
                low -= SEPEREMPAT
                high -= SEPEREMPAT
            else:
                break
            low <<= 1
            high = (high << 1) | 1
        model.perbarui(b)

    tertunda += 1
    keluarkan(0 if low < SEPEREMPAT else 1)

    # bit -> byte
    bit_keluar.extend([0] * (-len(bit_keluar) % 8))
    hasil = bytearray()
    for i in range(0, len(bit_keluar), 8):
        nilai = 0
        for bit in bit_keluar[i:i + 8]:
            nilai = (nilai << 1) | bit
        hasil.append(nilai)
    return bytes(hasil)


def dekode_aritmetika(kode, n, tambah, batas):
    model = Model(tambah, batas)
    total_bit = len(kode) * 8

    def bit_ke(i):
        # bit di luar data dianggap 0
        return (kode[i >> 3] >> (7 - (i & 7))) & 1 if i < total_bit else 0

    nilai = 0
    for i in range(BIT):
        nilai = (nilai << 1) | bit_ke(i)
    posisi = BIT

    low, high = 0, PENUH
    hasil = bytearray()
    for _ in range(n):
        rentang = high - low + 1
        target = ((nilai - low + 1) * model.total - 1) // rentang
        b = model.cari(target)
        cum_low = model.kumulatif(b)
        cum_high = cum_low + model.frek[b]
        high = low + rentang * cum_high // model.total - 1
        low = low + rentang * cum_low // model.total
        while True:
            if high < SETENGAH:
                pass
            elif low >= SETENGAH:
                low -= SETENGAH
                high -= SETENGAH
                nilai -= SETENGAH
            elif low >= SEPEREMPAT and high < TIGA_PEREMPAT:
                low -= SEPEREMPAT
                high -= SEPEREMPAT
                nilai -= SEPEREMPAT
            else:
                break
            low <<= 1
            high = (high << 1) | 1
            nilai = (nilai << 1) | bit_ke(posisi)
            posisi += 1
        hasil.append(b)
        model.perbarui(b)
    return bytes(hasil)


# ---------- format file .rma ----------

def encode(data, tambah=TAMBAH_DEFAULT, batas=BATAS_DEFAULT):
    if not 1 <= tambah <= 1 << 16:
        raise ValueError('Nilai tambah harus di antara 1 dan 65536')
    if not 512 <= batas <= 1 << 24:
        raise ValueError('Batas harus di antara 512 dan 16777216')
    header = MAGIC + rmh.tulis_varint(len(data)) + rmh.tulis_varint(tambah) + rmh.tulis_varint(batas)
    crc = zlib.crc32(data).to_bytes(4, 'big')
    kode = kode_aritmetika(data, tambah, batas) if data else b''
    rincian = {'header': len(header), 'crc32': len(crc), 'histogram': 0, 'kode (rank)': len(kode)}
    return header + crc + kode, rincian


def baca_rma(isi):
    if isi[:4] != MAGIC:
        raise ValueError('Bukan file .rma (magic tidak cocok)')
    pos = 4
    try:
        n, pos = rmh.baca_varint(isi, pos)
        tambah, pos = rmh.baca_varint(isi, pos)
        batas, pos = rmh.baca_varint(isi, pos)
    except ValueError:
        raise ValueError('File .rma terpotong (header tidak lengkap)')
    if not 1 <= tambah <= 1 << 16 or not 512 <= batas <= 1 << 24:
        raise ValueError('Parameter model tidak valid (tambah=%d, batas=%d)' % (tambah, batas))
    if pos + 4 > len(isi):
        raise ValueError('File .rma terpotong (CRC32 tidak lengkap)')
    crc = int.from_bytes(isi[pos:pos + 4], 'big')
    return n, tambah, batas, crc, isi[pos + 4:]


def decode(isi):
    n, tambah, batas, crc, kode = baca_rma(isi)
    data = dekode_aritmetika(kode, n, tambah, batas) if n else b''
    if zlib.crc32(data) != crc:
        raise ValueError('CRC32 tidak cocok, hasil decode rusak')
    return data


# ---------- perintah ----------

def cmd_encode(args):
    data = rmh.baca_file(args.input)
    output = args.output or args.input + '.rma'
    mulai = time.perf_counter()
    try:
        isi, rincian = encode(data, args.tambah, args.batas)
    except ValueError as e:
        sys.exit('Encode gagal: %s' % e)
    durasi = time.perf_counter() - mulai
    rmh.tulis_file(output, isi)

    n = len(data)
    print('Encode  :', args.input, '->', output, '(%.3f detik)' % durasi)
    print()
    print('Rincian file .rma:')
    for nama, ukuran in rincian.items():
        print('  %-12s %10d byte' % (nama, ukuran))
    print('  %-12s %10d byte' % ('TOTAL', len(isi)))
    print()
    print('Ukuran  : %d -> %d byte (%s dari asli)' % (n, len(isi), rmh.persen(len(isi), n)))


def cmd_decode(args):
    isi = rmh.baca_file(args.input)
    if args.output:
        output = args.output
    elif args.input.endswith('.rma'):
        output = args.input[:-4] + '.decoded'
    else:
        output = args.input + '.decoded'
    mulai = time.perf_counter()
    try:
        data = decode(isi)
    except ValueError as e:
        sys.exit('Decode gagal: %s' % e)
    durasi = time.perf_counter() - mulai
    rmh.tulis_file(output, data)
    print('Decode  :', args.input, '->', output, '(%.3f detik)' % durasi)
    print('Ukuran  :', len(data), 'byte, CRC32 cocok')


def cmd_bandingkan(args):
    import rmh_blok
    data = rmh.baca_file(args.input)
    n = len(data)
    print('File:', args.input, '(%d byte)' % n)
    print()
    print('%-26s %12s %12s %12s %9s' % ('Metode', 'Histogram', 'Rank/kode', 'Total', '% asli'))

    isi, r, _ = rmh_blok.encode(data, args.blok, jobs=1)
    print('%-26s %12d %12d %12d %9s' % ('.rmb (blok %d)' % args.blok, r['histogram'], r['rank'],
                                        len(isi), rmh.persen(len(isi), n)))
    isi, r = encode(data, args.tambah, args.batas)
    print('%-26s %12d %12d %12d %9s' % ('.rma (adaptif)', 0, r['kode (rank)'], len(isi), rmh.persen(len(isi), n)))
    z = len(zlib.compress(data, 9))
    x = len(lzma.compress(data, preset=9))
    print('%-26s %12s %12s %12d %9s' % ('zlib -9', '', '', z, rmh.persen(z, n)))
    print('%-26s %12s %12s %12d %9s' % ('lzma -9', '', '', x, rmh.persen(x, n)))


def main():
    parser = argparse.ArgumentParser(description='Return[er] Machine Hash adaptif: histogram dipelajari, tidak disimpan (.rma).')
    sub = parser.add_subparsers(dest='perintah', required=True)

    def opsi_model(p):
        p.add_argument('--tambah', type=int, default=TAMBAH_DEFAULT,
                       help='penambahan frekuensi tiap byte muncul (default: %d)' % TAMBAH_DEFAULT)
        p.add_argument('--batas', type=int, default=BATAS_DEFAULT,
                       help='total frekuensi maksimum sebelum dibagi dua (default: %d)' % BATAS_DEFAULT)

    p = sub.add_parser('encode', help='file asli -> file .rma')
    p.add_argument('input')
    p.add_argument('-o', '--output', help='nama file .rma (default: <input>.rma)')
    opsi_model(p)
    p.set_defaults(func=cmd_encode)

    p = sub.add_parser('decode', help='file .rma -> file asli')
    p.add_argument('input')
    p.add_argument('-o', '--output', help='nama file hasil (default: <input tanpa .rma>.decoded)')
    p.set_defaults(func=cmd_decode)

    p = sub.add_parser('bandingkan', help='bandingkan .rmb, .rma, zlib, lzma (tanpa menulis file)')
    p.add_argument('input')
    p.add_argument('-b', '--blok', type=int, default=4096, help='ukuran blok untuk .rmb (default: 4096)')
    opsi_model(p)
    p.set_defaults(func=cmd_bandingkan)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
