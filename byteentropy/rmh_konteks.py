import sys
import time
import zlib
import lzma
import argparse

import rmh
# rmh_konteks.py - Return[er] Machine Hash dengan konteks (PPM)
# Lanjutan rmh_adaptif.py: bukan lagi satu histogram untuk seluruh file, tetapi
# satu histogram adaptif PER KONTEKS. Konteks = 1..N byte sebelumnya.
# Contoh di teks: setelah "ban" byte "k" sangat mungkin muncul, setelah "q" hampir
# pasti "u". Histogram per konteks menangkap pola urutan seperti ini.
#
# Konteks yang panjang lebih tajam tebakannya tetapi sering belum pernah dilihat.
# Karena itu dipakai PPM (Prediction by Partial Matching):
#   1. coba konteks terpanjang (orde N);
#   2. jika byte belum pernah muncul di konteks itu, kodekan tanda ESCAPE lalu
#      turun ke konteks yang lebih pendek (orde N-1, ..., 0);
#   3. orde -1: semua 256 nilai byte berpeluang sama (pasti berhasil).
# Byte yang sudah gagal di konteks lebih panjang dikecualikan di konteks
# berikutnya (exclusion), sehingga peluangnya tidak terbuang.
#
# Format file .rmk (varint = LEB128):
#   [4 byte ] magic "RMK1"
#   [varint ] n          : ukuran file asli (byte)
#   [1 byte ] orde       : panjang konteks maksimum (0..ORDE_MAKS)
#   [4 byte ] CRC32 file asli
#   [sisa   ] bit hasil arithmetic coding

MAGIC = b'RMK1'
ORDE_DEFAULT = 3
ORDE_MAKS = 6
BATAS_KONTEKS = 1 << 13     # total frekuensi per konteks sebelum dibagi dua

# arithmetic coder 32-bit (Witten, Neal & Cleary 1987), sama seperti rmh_adaptif.py
BIT = 32
PENUH = (1 << BIT) - 1
SETENGAH = 1 << (BIT - 1)
SEPEREMPAT = 1 << (BIT - 2)
TIGA_PEREMPAT = 3 * SEPEREMPAT


# ---------- arithmetic coder ----------

class Encoder:
    def __init__(self):
        self.low, self.high, self.tertunda = 0, PENUH, 0
        self.bit = []

    def _keluarkan(self, bit):
        self.bit.append(bit)
        self.bit.extend([1 - bit] * self.tertunda)
        self.tertunda = 0

    def kodekan(self, cum_low, cum_high, total):
        rentang = self.high - self.low + 1
        self.high = self.low + rentang * cum_high // total - 1
        self.low = self.low + rentang * cum_low // total
        while True:
            if self.high < SETENGAH:
                self._keluarkan(0)
            elif self.low >= SETENGAH:
                self._keluarkan(1)
                self.low -= SETENGAH
                self.high -= SETENGAH
            elif self.low >= SEPEREMPAT and self.high < TIGA_PEREMPAT:
                self.tertunda += 1
                self.low -= SEPEREMPAT
                self.high -= SEPEREMPAT
            else:
                break
            self.low <<= 1
            self.high = (self.high << 1) | 1

    def selesai(self):
        self.tertunda += 1
        self._keluarkan(0 if self.low < SEPEREMPAT else 1)
        bit = self.bit + [0] * (-len(self.bit) % 8)
        hasil = bytearray()
        for i in range(0, len(bit), 8):
            nilai = 0
            for b in bit[i:i + 8]:
                nilai = (nilai << 1) | b
            hasil.append(nilai)
        return bytes(hasil)


class Decoder:
    def __init__(self, kode):
        self.kode = kode
        self.total_bit = len(kode) * 8
        self.posisi = 0
        self.low, self.high = 0, PENUH
        self.nilai = 0
        for _ in range(BIT):
            self.nilai = (self.nilai << 1) | self._bit()

    def _bit(self):
        i = self.posisi
        self.posisi += 1
        return (self.kode[i >> 3] >> (7 - (i & 7))) & 1 if i < self.total_bit else 0

    def target(self, total):
        rentang = self.high - self.low + 1
        return ((self.nilai - self.low + 1) * total - 1) // rentang

    def konsumsi(self, cum_low, cum_high, total):
        rentang = self.high - self.low + 1
        self.high = self.low + rentang * cum_high // total - 1
        self.low = self.low + rentang * cum_low // total
        while True:
            if self.high < SETENGAH:
                pass
            elif self.low >= SETENGAH:
                self.low -= SETENGAH
                self.high -= SETENGAH
                self.nilai -= SETENGAH
            elif self.low >= SEPEREMPAT and self.high < TIGA_PEREMPAT:
                self.low -= SEPEREMPAT
                self.high -= SEPEREMPAT
                self.nilai -= SEPEREMPAT
            else:
                break
            self.low <<= 1
            self.high = (self.high << 1) | 1
            self.nilai = (self.nilai << 1) | self._bit()


# ---------- model PPM ----------

class ModelPPM:
    # Setiap orde k punya kamus: konteks (k byte terakhir sebagai int) -> {byte: frekuensi}.
    # Peluang di satu konteks (metode escape PPM-D):
    #   byte x   : 2*frek(x) - 1
    #   escape   : jumlah byte berbeda di konteks itu
    #   total    : 2*jumlah frekuensi
    def __init__(self, orde):
        self.orde = orde
        self.tabel = [dict() for _ in range(orde + 1)]
        self.riwayat = 0
        self.panjang_riwayat = 0
        self.statistik = [0] * (orde + 2)   # berapa byte terkode di tiap orde (indeks -1 = terakhir)

    def daftar_konteks(self):
        # konteks dari orde terpanjang yang tersedia sampai orde 0
        hasil = []
        for k in range(min(self.orde, self.panjang_riwayat), -1, -1):
            kunci = self.riwayat & ((1 << (8 * k)) - 1)
            hasil.append((k, self.tabel[k].get(kunci)))
        return hasil

    def perbarui(self, x):
        for k in range(min(self.orde, self.panjang_riwayat) + 1):
            kunci = self.riwayat & ((1 << (8 * k)) - 1)
            konteks = self.tabel[k].get(kunci)
            if konteks is None:
                self.tabel[k][kunci] = {x: 1}
                continue
            konteks[x] = konteks.get(x, 0) + 1
            if konteks[x] > BATAS_KONTEKS // 2 or sum(konteks.values()) > BATAS_KONTEKS:
                for s in list(konteks):
                    konteks[s] = (konteks[s] + 1) // 2
        if self.orde:
            self.riwayat = ((self.riwayat << 8) | x) & ((1 << (8 * self.orde)) - 1)
        self.panjang_riwayat += 1

    def jumlah_konteks(self):
        return [len(t) for t in self.tabel]


def _interval(konteks, dikecualikan):
    # kembalikan daftar (byte, cum_low, cum_high), total_byte, total (termasuk escape)
    daftar = []
    cum = 0
    for s, f in konteks.items():
        if s in dikecualikan:
            continue
        lebar = 2 * f - 1
        daftar.append((s, cum, cum + lebar))
        cum += lebar
    berbeda = len(daftar)
    return daftar, cum, cum + berbeda


def kodekan_konteks(data, orde):
    model = ModelPPM(orde)
    enc = Encoder()
    for x in data:
        dikecualikan = set()
        berhasil = False
        for k, konteks in model.daftar_konteks():
            if not konteks:
                continue
            daftar, cum_byte, total = _interval(konteks, dikecualikan)
            if not daftar:
                continue
            for s, lo, hi in daftar:
                if s == x:
                    enc.kodekan(lo, hi, total)
                    model.statistik[k] += 1
                    berhasil = True
                    break
            if berhasil:
                break
            enc.kodekan(cum_byte, total, total)     # ESCAPE
            dikecualikan.update(s for s, _, _ in daftar)
        if not berhasil:
            # orde -1: peluang sama untuk semua byte yang belum dikecualikan
            sisa = [s for s in range(256) if s not in dikecualikan]
            i = sisa.index(x)
            enc.kodekan(i, i + 1, len(sisa))
            model.statistik[-1] += 1
        model.perbarui(x)
    return enc.selesai(), model


def dekode_konteks(kode, n, orde):
    model = ModelPPM(orde)
    dec = Decoder(kode)
    hasil = bytearray()
    for _ in range(n):
        dikecualikan = set()
        x = None
        for k, konteks in model.daftar_konteks():
            if not konteks:
                continue
            daftar, cum_byte, total = _interval(konteks, dikecualikan)
            if not daftar:
                continue
            t = dec.target(total)
            if t < cum_byte:
                for s, lo, hi in daftar:
                    if lo <= t < hi:
                        dec.konsumsi(lo, hi, total)
                        x = s
                        break
                break
            dec.konsumsi(cum_byte, total, total)    # ESCAPE
            dikecualikan.update(s for s, _, _ in daftar)
        if x is None:
            sisa = [s for s in range(256) if s not in dikecualikan]
            i = dec.target(len(sisa))
            if i >= len(sisa):
                raise ValueError('Kode rusak (indeks byte di luar jangkauan)')
            dec.konsumsi(i, i + 1, len(sisa))
            x = sisa[i]
        hasil.append(x)
        model.perbarui(x)
    return bytes(hasil)


# ---------- format file .rmk ----------

def encode(data, orde=ORDE_DEFAULT):
    if not 0 <= orde <= ORDE_MAKS:
        raise ValueError('Orde harus di antara 0 dan %d' % ORDE_MAKS)
    header = MAGIC + rmh.tulis_varint(len(data)) + bytes([orde])
    crc = zlib.crc32(data).to_bytes(4, 'big')
    if data:
        kode, model = kodekan_konteks(data, orde)
    else:
        kode, model = b'', ModelPPM(orde)
    rincian = {'header': len(header), 'crc32': len(crc), 'histogram': 0, 'kode (rank)': len(kode)}
    return header + crc + kode, rincian, model


def baca_rmk(isi):
    if isi[:4] != MAGIC:
        raise ValueError('Bukan file .rmk (magic tidak cocok)')
    try:
        n, pos = rmh.baca_varint(isi, 4)
    except ValueError:
        raise ValueError('File .rmk terpotong (header tidak lengkap)')
    if pos + 5 > len(isi):
        raise ValueError('File .rmk terpotong (header tidak lengkap)')
    orde = isi[pos]
    if orde > ORDE_MAKS:
        raise ValueError('Orde tidak valid: %d' % orde)
    crc = int.from_bytes(isi[pos + 1:pos + 5], 'big')
    return n, orde, crc, isi[pos + 5:]


def decode(isi):
    n, orde, crc, kode = baca_rmk(isi)
    data = dekode_konteks(kode, n, orde) if n else b''
    if zlib.crc32(data) != crc:
        raise ValueError('CRC32 tidak cocok, hasil decode rusak')
    return data


# ---------- perintah ----------

def cmd_encode(args):
    data = rmh.baca_file(args.input)
    output = args.output or args.input + '.rmk'
    mulai = time.perf_counter()
    try:
        isi, rincian, model = encode(data, args.orde)
    except ValueError as e:
        sys.exit('Encode gagal: %s' % e)
    durasi = time.perf_counter() - mulai
    rmh.tulis_file(output, isi)

    n = len(data)
    print('Encode  :', args.input, '->', output, '(%.3f detik, orde %d)' % (durasi, args.orde))
    print()
    print('Rincian file .rmk:')
    for nama, ukuran in rincian.items():
        print('  %-12s %10d byte' % (nama, ukuran))
    print('  %-12s %10d byte' % ('TOTAL', len(isi)))
    print()
    print('Ukuran  : %d -> %d byte (%s dari asli)' % (n, len(isi), rmh.persen(len(isi), n)))
    if n:
        print()
        print('Byte berhasil ditebak di konteks orde:')
        for k in range(args.orde, -1, -1):
            print('  orde %2d : %8d byte (%5.1f%%)  dari %d konteks' % (
                k, model.statistik[k], model.statistik[k] / n * 100, model.jumlah_konteks()[k]))
        print('  orde -1 : %8d byte (%5.1f%%)  byte yang benar-benar baru' % (
            model.statistik[-1], model.statistik[-1] / n * 100))


def cmd_decode(args):
    isi = rmh.baca_file(args.input)
    if args.output:
        output = args.output
    elif args.input.endswith('.rmk'):
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
    import rmh_adaptif
    data = rmh.baca_file(args.input)
    n = len(data)
    print('File:', args.input, '(%d byte)' % n)
    print()
    print('%-22s %12s %9s %10s' % ('Metode', 'Ukuran', '% asli', 'Detik'))

    def baris(nama, fungsi):
        mulai = time.perf_counter()
        ukuran = len(fungsi())
        print('%-22s %12d %9s %10.3f' % (nama, ukuran, rmh.persen(ukuran, n), time.perf_counter() - mulai))

    baris('.rmb (blok 4096)', lambda: rmh_blok.encode(data, 4096, jobs=1)[0])
    baris('.rma (adaptif)', lambda: rmh_adaptif.encode(data)[0])
    for k in args.orde:
        baris('.rmk orde %d' % k, lambda: encode(data, k)[0])
    baris('zlib -9', lambda: zlib.compress(data, 9))
    baris('lzma -9', lambda: lzma.compress(data, preset=9))


def main():
    parser = argparse.ArgumentParser(description='Return[er] Machine Hash dengan konteks PPM (.rmk).')
    sub = parser.add_subparsers(dest='perintah', required=True)

    p = sub.add_parser('encode', help='file asli -> file .rmk')
    p.add_argument('input')
    p.add_argument('-o', '--output', help='nama file .rmk (default: <input>.rmk)')
    p.add_argument('-k', '--orde', type=int, default=ORDE_DEFAULT,
                   help='panjang konteks maksimum 0..%d (default: %d)' % (ORDE_MAKS, ORDE_DEFAULT))
    p.set_defaults(func=cmd_encode)

    p = sub.add_parser('decode', help='file .rmk -> file asli')
    p.add_argument('input')
    p.add_argument('-o', '--output', help='nama file hasil (default: <input tanpa .rmk>.decoded)')
    p.set_defaults(func=cmd_decode)

    p = sub.add_parser('bandingkan', help='bandingkan .rmb, .rma, .rmk, zlib, lzma (tanpa menulis file)')
    p.add_argument('input')
    p.add_argument('-k', '--orde', type=int, nargs='+', default=[1, 2, 3, 4],
                   help='daftar orde yang dicoba (default: 1 2 3 4)')
    p.set_defaults(func=cmd_bandingkan)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
