import sys
import time
import zlib
import lzma
import argparse

import rmh
import rmh_konteks as rk
# rmh_konteks2.py - Return[er] Machine Hash dengan konteks (PPM), format RMK2
# Lanjutan rmh_konteks.py. Jumlah ESCAPE tidak bisa dikurangi (byte memang belum
# pernah muncul di konteks itu), tetapi HARGA tiap ESCAPE dan tiap byte bisa:
#
#   1. SEE (Secondary Escape Estimation, seperti PPMd/PPMZ).
#      Di RMK1 peluang ESCAPE memakai rumus tetap PPM-D: byte berbeda / total.
#      Di RMK2 peluang ESCAPE DIPELAJARI: tabel kecil mencatat seberapa sering
#      ESCAPE benar-benar terjadi pada situasi serupa, dengan kunci
#        (orde, orde tertinggi?, byte berbeda, total frekuensi, ada pengecualian?,
#         byte sebelumnya ESCAPE dari orde tertinggi?)
#      Awalnya tabel kosong, sehingga tebakan sama dengan PPM-D. Tabel dipelajari
#      encoder dan decoder bersama-sama, jadi tidak disimpan di file (0 byte).
#
#   2. Update exclusion.
#      Di RMK1 frekuensi byte ditambah di SEMUA orde. Di RMK2 hanya di orde yang
#      berhasil menebak dan orde di atasnya. Orde rendah hanya belajar dari byte
#      yang benar-benar sampai ke sana (setelah ESCAPE), sehingga lebih tajam
#      tepat pada saat dibutuhkan.
#
# Semua hitungan memakai bilangan bulat, jadi hasilnya sama di semua komputer.
#
# Format file .rmk versi 2 (varint = LEB128), sama dengan RMK1 kecuali magic:
#   [4 byte ] magic "RMK2"
#   [varint ] n          : ukuran file asli (byte)
#   [1 byte ] orde       : panjang konteks maksimum (0..ORDE_MAKS)
#   [4 byte ] CRC32 file asli
#   [sisa   ] bit hasil arithmetic coding
# decode juga bisa membuka file RMK1.

MAGIC = b'RMK2'
ORDE_DEFAULT = 5
ORDE_MAKS = rk.ORDE_MAKS
BATAS_KONTEKS = rk.BATAS_KONTEKS

SKALA = 1 << 16             # total frekuensi tiap langkah kode di sebuah konteks
ESC_MIN = SKALA >> 12       # peluang ESCAPE paling kecil 1/4096
SEE_SATU = 16               # 1 kejadian di tabel SEE (pecahan 1/16 saat dibagi dua)
SEE_BATAS = 256 * SEE_SATU  # jumlah kejadian per kunci sebelum dibagi dua
SEE_BOBOT = 2 * SEE_SATU    # bobot tebakan PPM-D sebagai titik awal


# ---------- model PPM dengan SEE dan update exclusion ----------

class ModelPPM2:
    # Setiap orde k punya kamus: konteks (k byte terakhir sebagai int) -> {byte: frekuensi}.
    # Di dalam satu konteks:
    #   lebar byte x : 2*frek(x) - 1           (sama dengan PPM-D)
    #   ESCAPE       : dari tabel SEE, lalu semua lebar diskalakan ke total SKALA
    def __init__(self, orde):
        self.orde = orde
        self.tabel = [dict() for _ in range(orde + 1)]
        self.see = {}                       # kunci -> [escape, kunjungan] dalam satuan SEE_SATU
        self.riwayat = 0
        self.panjang_riwayat = 0
        self.escape_sebelumnya = 0          # 1 jika byte sebelumnya tidak tertebak di orde tertinggi
        self.statistik = [0] * (orde + 2)   # berapa byte terkode di tiap orde (indeks -1 = terakhir)
        self.jumlah_escape = 0

    def daftar_konteks(self):
        # konteks dari orde terpanjang yang tersedia sampai orde 0
        hasil = []
        for k in range(min(self.orde, self.panjang_riwayat), -1, -1):
            kunci = self.riwayat & ((1 << (8 * k)) - 1)
            hasil.append((k, self.tabel[k].get(kunci)))
        return hasil

    def langkah(self, k, konteks, dikecualikan):
        # kembalikan daftar (byte, cum_low, cum_high) yang sudah diskalakan, batas awal
        # ESCAPE (= total lebar byte), dan kunci SEE. Total selalu SKALA.
        daftar = []
        cum = 0
        jumlah = 0
        for s, f in konteks.items():
            if s in dikecualikan:
                continue
            lebar = 2 * f - 1
            daftar.append((s, cum, cum + lebar))
            cum += lebar
            jumlah += f
        if not daftar:
            return None, 0, None
        d = len(daftar)
        kunci = (min(k, 3), k == self.orde, min(d, 6), min(jumlah.bit_length() - 1, 9),
                 bool(dikecualikan), self.escape_sebelumnya)
        e, kunjungan = self.see.get(kunci, (0, 0))
        # campuran pengalaman SEE dengan tebakan PPM-D d/(cum+d); tanpa pengalaman = PPM-D
        esc = (e * (cum + d) + SEE_BOBOT * d) * SKALA // ((kunjungan + SEE_BOBOT) * (cum + d))
        # setiap byte harus tetap punya lebar minimal 1 setelah diskalakan: SKALA - esc >= cum
        esc = max(ESC_MIN, min(esc, SKALA - max(cum, ESC_MIN)))
        ruang = SKALA - esc
        daftar = [(s, lo * ruang // cum, hi * ruang // cum) for s, lo, hi in daftar]
        return daftar, ruang, kunci

    def catat_see(self, kunci, escape):
        e, kunjungan = self.see.get(kunci, (0, 0))
        if escape:
            e += SEE_SATU
        kunjungan += SEE_SATU
        if kunjungan > SEE_BATAS:
            e >>= 1
            kunjungan >>= 1
        self.see[kunci] = (e, kunjungan)

    def perbarui(self, x, orde_tebak):
        # update exclusion: frekuensi hanya ditambah di orde >= orde yang menebak.
        # Konteks yang belum ada tetap dibuat di semua orde.
        tertinggi = min(self.orde, self.panjang_riwayat)
        bawah = max(orde_tebak, 0)
        for k in range(tertinggi + 1):
            kunci = self.riwayat & ((1 << (8 * k)) - 1)
            konteks = self.tabel[k].get(kunci)
            if konteks is None:
                self.tabel[k][kunci] = {x: 1}
                continue
            if k < bawah:
                continue
            konteks[x] = konteks.get(x, 0) + 1
            if konteks[x] > BATAS_KONTEKS // 2 or sum(konteks.values()) > BATAS_KONTEKS:
                for s in list(konteks):
                    konteks[s] = (konteks[s] + 1) // 2
        self.escape_sebelumnya = int(orde_tebak != tertinggi)
        if orde_tebak >= 0:
            self.statistik[orde_tebak] += 1
        else:
            self.statistik[-1] += 1
        if self.orde:
            self.riwayat = ((self.riwayat << 8) | x) & ((1 << (8 * self.orde)) - 1)
        self.panjang_riwayat += 1

    def jumlah_konteks(self):
        return [len(t) for t in self.tabel]


def kodekan_konteks(data, orde):
    model = ModelPPM2(orde)
    enc = rk.Encoder()
    for x in data:
        dikecualikan = set()
        orde_tebak = -1
        for k, konteks in model.daftar_konteks():
            if not konteks:
                continue
            daftar, ruang, kunci = model.langkah(k, konteks, dikecualikan)
            if not daftar:
                continue
            for s, lo, hi in daftar:
                if s == x:
                    enc.kodekan(lo, hi, SKALA)
                    orde_tebak = k
                    break
            model.catat_see(kunci, orde_tebak < 0)
            if orde_tebak >= 0:
                break
            enc.kodekan(ruang, SKALA, SKALA)        # ESCAPE
            model.jumlah_escape += 1
            dikecualikan.update(s for s, _, _ in daftar)
        if orde_tebak < 0:
            # orde -1: peluang sama untuk semua byte yang belum dikecualikan
            sisa = [s for s in range(256) if s not in dikecualikan]
            i = sisa.index(x)
            enc.kodekan(i, i + 1, len(sisa))
        model.perbarui(x, orde_tebak)
    return enc.selesai(), model


def dekode_konteks(kode, n, orde):
    model = ModelPPM2(orde)
    dec = rk.Decoder(kode)
    hasil = bytearray()
    for _ in range(n):
        dikecualikan = set()
        x = None
        orde_tebak = -1
        for k, konteks in model.daftar_konteks():
            if not konteks:
                continue
            daftar, ruang, kunci = model.langkah(k, konteks, dikecualikan)
            if not daftar:
                continue
            t = dec.target(SKALA)
            if t < ruang:
                for s, lo, hi in daftar:
                    if lo <= t < hi:
                        dec.konsumsi(lo, hi, SKALA)
                        x = s
                        orde_tebak = k
                        break
                model.catat_see(kunci, False)
                break
            model.catat_see(kunci, True)
            dec.konsumsi(ruang, SKALA, SKALA)       # ESCAPE
            model.jumlah_escape += 1
            dikecualikan.update(s for s, _, _ in daftar)
        if x is None:
            sisa = [s for s in range(256) if s not in dikecualikan]
            i = dec.target(len(sisa))
            if i >= len(sisa):
                raise ValueError('Kode rusak (indeks byte di luar jangkauan)')
            dec.konsumsi(i, i + 1, len(sisa))
            x = sisa[i]
        hasil.append(x)
        model.perbarui(x, orde_tebak)
    return bytes(hasil)


# ---------- format file .rmk versi 2 ----------

def encode(data, orde=ORDE_DEFAULT):
    if not 0 <= orde <= ORDE_MAKS:
        raise ValueError('Orde harus di antara 0 dan %d' % ORDE_MAKS)
    header = MAGIC + rmh.tulis_varint(len(data)) + bytes([orde])
    crc = zlib.crc32(data).to_bytes(4, 'big')
    if data:
        kode, model = kodekan_konteks(data, orde)
    else:
        kode, model = b'', ModelPPM2(orde)
    rincian = {'header': len(header), 'crc32': len(crc), 'histogram': 0, 'kode (rank)': len(kode)}
    return header + crc + kode, rincian, model


def baca_rmk(isi):
    if isi[:4] != MAGIC:
        raise ValueError('Bukan file .rmk versi 2 (magic tidak cocok)')
    # selain magic, header RMK2 sama dengan RMK1
    return rk.baca_rmk(rk.MAGIC + isi[4:])


def decode(isi):
    if isi[:4] == rk.MAGIC:
        return rk.decode(isi)
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
    print('Encode  :', args.input, '->', output, '(%.3f detik, orde %d, RMK2)' % (durasi, args.orde))
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
        print()
        print('ESCAPE  : %d kali, tabel SEE %d kunci (dipelajari, tidak disimpan)' % (
            model.jumlah_escape, len(model.see)))

    if args.verifikasi:
        if decode(isi) != data:
            sys.exit('Verifikasi GAGAL: hasil decode berbeda dengan file asli')
        print('Verifikasi: decode ulang identik dengan file asli')


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
    print('Decode  :', args.input, '->', output, '(%.3f detik, %s)' % (durasi, isi[:4].decode('ascii', 'replace')))
    print('Ukuran  :', len(data), 'byte, CRC32 cocok')


def cmd_bandingkan(args):
    data = rmh.baca_file(args.input)
    n = len(data)
    print('File:', args.input, '(%d byte)' % n)
    print()
    print('%-22s %12s %9s %10s' % ('Metode', 'Ukuran', '% asli', 'Detik'))

    def baris(nama, fungsi):
        mulai = time.perf_counter()
        ukuran = len(fungsi())
        print('%-22s %12d %9s %10.3f' % (nama, ukuran, rmh.persen(ukuran, n), time.perf_counter() - mulai))

    for k in args.orde:
        baris('RMK1 orde %d' % k, lambda: rk.encode(data, k)[0])
        baris('RMK2 orde %d' % k, lambda: encode(data, k)[0])
    baris('zlib -9', lambda: zlib.compress(data, 9))
    baris('lzma -9', lambda: lzma.compress(data, preset=9))


def main():
    parser = argparse.ArgumentParser(
        description='Return[er] Machine Hash dengan konteks PPM + SEE + update exclusion (.rmk versi 2).')
    sub = parser.add_subparsers(dest='perintah', required=True)

    p = sub.add_parser('encode', help='file asli -> file .rmk versi 2')
    p.add_argument('input')
    p.add_argument('-o', '--output', help='nama file .rmk (default: <input>.rmk)')
    p.add_argument('-k', '--orde', type=int, default=ORDE_DEFAULT,
                   help='panjang konteks maksimum 0..%d (default: %d)' % (ORDE_MAKS, ORDE_DEFAULT))
    p.add_argument('--verifikasi', action='store_true', help='decode ulang dan bandingkan dengan file asli')
    p.set_defaults(func=cmd_encode)

    p = sub.add_parser('decode', help='file .rmk (versi 1 atau 2) -> file asli')
    p.add_argument('input')
    p.add_argument('-o', '--output', help='nama file hasil (default: <input tanpa .rmk>.decoded)')
    p.set_defaults(func=cmd_decode)

    p = sub.add_parser('bandingkan', help='bandingkan RMK1, RMK2, zlib, lzma (tanpa menulis file)')
    p.add_argument('input')
    p.add_argument('-k', '--orde', type=int, nargs='+', default=[3, 4, 5],
                   help='daftar orde yang dicoba (default: 3 4 5)')
    p.set_defaults(func=cmd_bandingkan)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
