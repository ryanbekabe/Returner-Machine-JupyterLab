import sys
import time
import zlib
import lzma
import argparse

import numpy as np
from numba import njit

import rmh
import rmh_konteks as rk
import rmh_konteks2 as rk2
# rmh_konteks3.py - versi CEPAT dari rmh_konteks2.py (format RMK2 yang sama persis)
# Model dan arithmetic coder sama dengan rmh_konteks2.py (PPM + SEE + update exclusion),
# hanya ditulis ulang untuk numba (dikompilasi ke kode mesin). Hasil encode IDENTIK
# byte demi byte dengan rmh_konteks2.py, sehingga file dari keduanya bisa saling dibuka.
#
# Struktur data pengganti dict Python:
#   - tabel konteks : hash table (open addressing), kunci = (k byte terakhir) * 8 + orde
#   - isi konteks   : blok array (byte, frekuensi) yang bersebelahan di memori, sesuai
#                     urutan kemunculan pertama (sama dengan urutan dict Python), sehingga
#                     interval kode sama persis. Blok penuh dipindah ke blok 2x lebih besar.
#   - tabel SEE     : array 4 x 2 x 7 x 10 x 2 x 2 (kunci SEE yang sama dengan RMK2)
# Kompilasi pertama butuh beberapa detik; hasilnya di-cache di __pycache__.

ORDE_DEFAULT = rk2.ORDE_DEFAULT
ORDE_MAKS = rk2.ORDE_MAKS

PENUH = (1 << 32) - 1
SETENGAH = 1 << 31
SEPEREMPAT = 1 << 30
TIGA_PEREMPAT = 3 << 30

SKALA = rk2.SKALA
ESC_MIN = rk2.ESC_MIN
SEE_SATU = rk2.SEE_SATU
SEE_BATAS = rk2.SEE_BATAS
SEE_BOBOT = rk2.SEE_BOBOT
BATAS_KONTEKS = rk2.BATAS_KONTEKS
JUMLAH_SEE = 4 * 2 * 7 * 10 * 2 * 2

KODE_RUSAK = 1


# ---------- arithmetic coder (sama dengan rmh_konteks.py, 32-bit) ----------
# st = [low, high, tertunda (encode) / nilai (decode), jumlah bit ditulis / posisi bit dibaca]

@njit(cache=True, nogil=True)
def _tulis_bit(out, st, bit):
    pos = st[3]
    if (pos >> 3) + 1 >= out.shape[0]:
        baru = np.zeros(out.shape[0] * 2, np.uint8)
        baru[:out.shape[0]] = out
        out = baru
    if bit:
        out[pos >> 3] |= np.uint8(0x80 >> (pos & 7))
    st[3] = pos + 1
    return out


@njit(cache=True, nogil=True)
def _keluarkan(out, st, bit):
    out = _tulis_bit(out, st, bit)
    while st[2] > 0:
        out = _tulis_bit(out, st, 1 - bit)
        st[2] -= 1
    return out


@njit(cache=True, nogil=True)
def _kodekan(out, st, cum_low, cum_high, total):
    rentang = st[1] - st[0] + 1
    st[1] = st[0] + rentang * cum_high // total - 1
    st[0] = st[0] + rentang * cum_low // total
    while True:
        if st[1] < SETENGAH:
            out = _keluarkan(out, st, 0)
        elif st[0] >= SETENGAH:
            out = _keluarkan(out, st, 1)
            st[0] -= SETENGAH
            st[1] -= SETENGAH
        elif st[0] >= SEPEREMPAT and st[1] < TIGA_PEREMPAT:
            st[2] += 1
            st[0] -= SEPEREMPAT
            st[1] -= SEPEREMPAT
        else:
            break
        st[0] <<= 1
        st[1] = (st[1] << 1) | 1
    return out


@njit(cache=True, nogil=True)
def _baca_bit(kode, st):
    i = st[3]
    st[3] = i + 1
    if i < kode.shape[0] * 8:
        return (kode[i >> 3] >> (7 - (i & 7))) & 1
    return 0


@njit(cache=True, nogil=True)
def _target(st, total):
    rentang = st[1] - st[0] + 1
    return ((st[2] - st[0] + 1) * total - 1) // rentang


@njit(cache=True, nogil=True)
def _konsumsi(kode, st, cum_low, cum_high, total):
    rentang = st[1] - st[0] + 1
    st[1] = st[0] + rentang * cum_high // total - 1
    st[0] = st[0] + rentang * cum_low // total
    while True:
        if st[1] < SETENGAH:
            pass
        elif st[0] >= SETENGAH:
            st[0] -= SETENGAH
            st[1] -= SETENGAH
            st[2] -= SETENGAH
        elif st[0] >= SEPEREMPAT and st[1] < TIGA_PEREMPAT:
            st[0] -= SEPEREMPAT
            st[1] -= SEPEREMPAT
            st[2] -= SEPEREMPAT
        else:
            break
        st[0] <<= 1
        st[1] = (st[1] << 1) | 1
        st[2] = (st[2] << 1) | _baca_bit(kode, st)


# ---------- hash table konteks ----------

@njit(cache=True, nogil=True)
def _slot(hkey, bit_cap, key):
    # posisi kunci di tabel, atau posisi kosong tempat kunci itu akan disisipkan
    mask = (1 << bit_cap) - 1
    h = np.int64((np.uint64(key) * np.uint64(11400714819323198485)) >> np.uint64(64 - bit_cap))
    while hkey[h] != -1 and hkey[h] != key:
        h = (h + 1) & mask
    return h


@njit(cache=True, nogil=True)
def _perbesar_tabel(hkey, hval, bit_cap):
    bit_baru = bit_cap + 1
    kunci_baru = np.full(1 << bit_baru, -1, np.int64)
    nilai_baru = np.empty(1 << bit_baru, np.int32)
    for i in range(hkey.shape[0]):
        if hkey[i] != -1:
            s = _slot(kunci_baru, bit_baru, hkey[i])
            kunci_baru[s] = hkey[i]
            nilai_baru[s] = hval[i]
    return kunci_baru, nilai_baru, bit_baru


@njit(cache=True, nogil=True)
def _perbesar_i32(a):
    b = np.empty(a.shape[0] * 2, np.int32)
    b[:a.shape[0]] = a
    return b


# ---------- model PPM2 + coder, satu fungsi untuk encode dan decode ----------

@njit(cache=True, nogil=True)
def _ppm2(data, n, orde, kode, dekode):
    # encode: data = byte asli, kode diabaikan. decode: kode = bit arithmetic coding.
    # Mengembalikan (hasil, panjang hasil, statistik, jumlah konteks, jumlah escape, kunci SEE, galat)
    masker = np.zeros(ORDE_MAKS + 1, np.int64)
    for k in range(ORDE_MAKS + 1):
        masker[k] = (1 << (8 * k)) - 1

    bit_cap = 16
    hkey = np.full(1 << bit_cap, -1, np.int64)
    hval = np.empty(1 << bit_cap, np.int32)
    n_ctx = 0
    c_mulai = np.empty(1 << 15, np.int32)     # posisi blok konteks di p_byte / p_frek
    c_kap = np.empty(1 << 15, np.int32)       # kapasitas blok
    c_isi = np.empty(1 << 15, np.int32)       # jumlah byte berbeda di konteks
    c_total = np.empty(1 << 15, np.int32)     # jumlah frekuensi
    n_pool = 0
    p_byte = np.empty(1 << 16, np.int32)
    p_frek = np.empty(1 << 16, np.int32)

    see_e = np.zeros(JUMLAH_SEE, np.int64)
    see_n = np.zeros(JUMLAH_SEE, np.int64)
    see_dipakai = np.zeros(JUMLAH_SEE, np.uint8)
    jumlah_see = 0

    statistik = np.zeros(orde + 2, np.int64)
    jumlah_konteks = np.zeros(orde + 1, np.int64)
    jumlah_escape = 0

    dikecualikan = np.zeros(256, np.uint8)
    daftar_kecuali = np.empty(256, np.int32)
    t_byte = np.empty(256, np.int32)
    t_lo = np.empty(256, np.int64)
    t_hi = np.empty(256, np.int64)
    ctx_orde = np.full(orde + 1, -1, np.int32)

    st = np.zeros(4, np.int64)
    st[1] = PENUH
    if dekode:
        hasil = np.empty(n, np.uint8)
        for _ in range(32):
            st[2] = (st[2] << 1) | _baca_bit(kode, st)
    else:
        hasil = np.zeros(n // 2 + 1024, np.uint8)

    riwayat = 0
    escape_sebelumnya = 0
    for i in range(n):
        tertinggi = min(orde, i)
        n_kecuali = 0
        orde_tebak = -1
        x = -1 if dekode else np.int64(data[i])

        # cari konteks di setiap orde sekali saja (dipakai lagi saat memperbarui)
        for k in range(tertinggi + 1):
            key = (riwayat & masker[k]) * 8 + k
            s = _slot(hkey, bit_cap, key)
            ctx_orde[k] = hval[s] if hkey[s] == key else -1

        for k in range(tertinggi, -1, -1):
            ci = ctx_orde[k]
            if ci < 0:
                continue
            d = 0
            cum = 0
            jumlah = 0
            awal = c_mulai[ci]
            for j in range(awal, awal + c_isi[ci]):
                b = p_byte[j]
                if dikecualikan[b] == 0:
                    f = p_frek[j]
                    t_byte[d] = b
                    t_lo[d] = cum
                    cum += 2 * f - 1
                    t_hi[d] = cum
                    jumlah += f
                    d += 1
            if d == 0:
                continue

            pangkat = 0
            v = jumlah
            while v > 1:
                v >>= 1
                pangkat += 1
            kunci = min(k, 3)
            kunci = kunci * 2 + (1 if k == orde else 0)
            kunci = kunci * 7 + min(d, 6)
            kunci = kunci * 10 + min(pangkat, 9)
            kunci = kunci * 2 + (1 if n_kecuali > 0 else 0)
            kunci = kunci * 2 + escape_sebelumnya

            e = see_e[kunci]
            kunjungan = see_n[kunci]
            esc = (e * (cum + d) + SEE_BOBOT * d) * SKALA // ((kunjungan + SEE_BOBOT) * (cum + d))
            esc = max(ESC_MIN, min(esc, SKALA - max(cum, ESC_MIN)))
            ruang = SKALA - esc

            if dekode:
                t = _target(st, SKALA)
                if t < ruang:
                    for j in range(d):
                        lo = t_lo[j] * ruang // cum
                        hi = t_hi[j] * ruang // cum
                        if lo <= t < hi:
                            _konsumsi(kode, st, lo, hi, SKALA)
                            x = t_byte[j]
                            orde_tebak = k
                            break
            else:
                for j in range(d):
                    if t_byte[j] == x:
                        hasil = _kodekan(hasil, st, t_lo[j] * ruang // cum, t_hi[j] * ruang // cum, SKALA)
                        orde_tebak = k
                        break

            if see_dipakai[kunci] == 0:
                see_dipakai[kunci] = 1
                jumlah_see += 1
            if orde_tebak < 0:
                e += SEE_SATU
            kunjungan += SEE_SATU
            if kunjungan > SEE_BATAS:
                e >>= 1
                kunjungan >>= 1
            see_e[kunci] = e
            see_n[kunci] = kunjungan
            if orde_tebak >= 0:
                break

            # ESCAPE
            if dekode:
                _konsumsi(kode, st, ruang, SKALA, SKALA)
            else:
                hasil = _kodekan(hasil, st, ruang, SKALA, SKALA)
            jumlah_escape += 1
            for j in range(d):
                dikecualikan[t_byte[j]] = 1
                daftar_kecuali[n_kecuali] = t_byte[j]
                n_kecuali += 1

        if orde_tebak < 0:
            # orde -1: peluang sama untuk semua byte yang belum dikecualikan
            total = 256 - n_kecuali
            if dekode:
                idx = _target(st, total)
                if idx >= total:
                    return hasil, 0, statistik, jumlah_konteks, jumlah_escape, jumlah_see, KODE_RUSAK
                _konsumsi(kode, st, idx, idx + 1, total)
                urutan = -1
                for b in range(256):
                    if dikecualikan[b] == 0:
                        urutan += 1
                        if urutan == idx:
                            x = b
                            break
            else:
                idx = 0
                for b in range(x):
                    if dikecualikan[b] == 0:
                        idx += 1
                hasil = _kodekan(hasil, st, idx, idx + 1, total)
            statistik[orde + 1] += 1
        else:
            statistik[orde_tebak] += 1
        for j in range(n_kecuali):
            dikecualikan[daftar_kecuali[j]] = 0
        if dekode:
            hasil[i] = x

        # perbarui model (update exclusion: hanya orde >= orde yang menebak)
        bawah = max(orde_tebak, 0)
        for k in range(tertinggi + 1):
            ci = ctx_orde[k]
            if ci < 0:
                # konteks baru {x: 1}, tetap dibuat di semua orde
                if n_ctx >= c_mulai.shape[0]:
                    c_mulai = _perbesar_i32(c_mulai)
                    c_kap = _perbesar_i32(c_kap)
                    c_isi = _perbesar_i32(c_isi)
                    c_total = _perbesar_i32(c_total)
                while n_pool + 1 > p_byte.shape[0]:
                    p_byte = _perbesar_i32(p_byte)
                    p_frek = _perbesar_i32(p_frek)
                p_byte[n_pool] = x
                p_frek[n_pool] = 1
                c_mulai[n_ctx] = n_pool
                c_kap[n_ctx] = 1
                c_isi[n_ctx] = 1
                c_total[n_ctx] = 1
                n_pool += 1
                if 2 * (n_ctx + 1) > hkey.shape[0]:
                    hkey, hval, bit_cap = _perbesar_tabel(hkey, hval, bit_cap)
                key = (riwayat & masker[k]) * 8 + k
                s = _slot(hkey, bit_cap, key)
                hkey[s] = key
                hval[s] = n_ctx
                n_ctx += 1
                jumlah_konteks[k] += 1
                continue
            if k < bawah:
                continue
            awal = c_mulai[ci]
            isi = c_isi[ci]
            pos = awal
            while pos < awal + isi and p_byte[pos] != x:
                pos += 1
            if pos == awal + isi:
                # byte baru di konteks ini: tambahkan di akhir blok (urutan tetap)
                if isi == c_kap[ci]:
                    kap = min(2 * isi, 256)
                    while n_pool + kap > p_byte.shape[0]:
                        p_byte = _perbesar_i32(p_byte)
                        p_frek = _perbesar_i32(p_frek)
                    p_byte[n_pool:n_pool + isi] = p_byte[awal:awal + isi]
                    p_frek[n_pool:n_pool + isi] = p_frek[awal:awal + isi]
                    awal = n_pool
                    c_mulai[ci] = awal
                    c_kap[ci] = kap
                    n_pool += kap
                pos = awal + isi
                p_byte[pos] = x
                p_frek[pos] = 0
                c_isi[ci] = isi + 1
            p_frek[pos] += 1
            c_total[ci] += 1
            if p_frek[pos] > BATAS_KONTEKS // 2 or c_total[ci] > BATAS_KONTEKS:
                total = 0
                for j in range(awal, awal + c_isi[ci]):
                    p_frek[j] = (p_frek[j] + 1) // 2
                    total += p_frek[j]
                c_total[ci] = total

        escape_sebelumnya = 1 if orde_tebak != tertinggi else 0
        if orde:
            riwayat = ((riwayat << 8) | x) & masker[orde]

    if dekode:
        return hasil, n, statistik, jumlah_konteks, jumlah_escape, jumlah_see, 0
    # selesai(): sama dengan Encoder.selesai di rmh_konteks.py
    st[2] += 1
    hasil = _keluarkan(hasil, st, 0 if st[0] < SEPEREMPAT else 1)
    return hasil, (st[3] + 7) >> 3, statistik, jumlah_konteks, jumlah_escape, jumlah_see, 0


# ---------- antarmuka Python (sama dengan rmh_konteks2.py) ----------

class Statistik:
    # pengganti objek model rmh_konteks2 untuk keperluan tampilan
    def __init__(self, statistik, jumlah_konteks, jumlah_escape, jumlah_see):
        self.statistik = [int(v) for v in statistik]
        self._jumlah_konteks = [int(v) for v in jumlah_konteks]
        self.jumlah_escape = int(jumlah_escape)
        self.jumlah_see = int(jumlah_see)

    def jumlah_konteks(self):
        return self._jumlah_konteks


def _cek_orde(orde):
    if not 0 <= orde <= ORDE_MAKS:
        raise ValueError('Orde harus di antara 0 dan %d' % ORDE_MAKS)


def kodekan_konteks(data, orde):
    _cek_orde(orde)
    arr = np.frombuffer(bytes(data), np.uint8)
    hasil, panjang, stat, ctx, esc, see, _ = _ppm2(arr, len(arr), orde, np.zeros(1, np.uint8), False)
    return hasil[:panjang].tobytes(), Statistik(stat, ctx, esc, see)


def dekode_konteks(kode, n, orde):
    _cek_orde(orde)
    arr = np.frombuffer(bytes(kode), np.uint8) if kode else np.zeros(0, np.uint8)
    hasil, panjang, _, _, _, _, galat = _ppm2(np.zeros(1, np.uint8), n, orde, arr, True)
    if galat == KODE_RUSAK:
        raise ValueError('Kode rusak (indeks byte di luar jangkauan)')
    return hasil[:panjang].tobytes()


def encode(data, orde=ORDE_DEFAULT):
    _cek_orde(orde)
    header = rk2.MAGIC + rmh.tulis_varint(len(data)) + bytes([orde])
    crc = zlib.crc32(data).to_bytes(4, 'big')
    if data:
        kode, model = kodekan_konteks(data, orde)
    else:
        kode, model = b'', Statistik([0] * (orde + 2), [0] * (orde + 1), 0, 0)
    rincian = {'header': len(header), 'crc32': len(crc), 'histogram': 0, 'kode (rank)': len(kode)}
    return header + crc + kode, rincian, model


def decode(isi):
    if isi[:4] == rk.MAGIC:
        return rk.decode(isi)       # RMK1 tetap memakai versi Python
    n, orde, crc, kode = rk2.baca_rmk(isi)
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
    print('Encode  :', args.input, '->', output, '(%.3f detik, orde %d, RMK2, numba)' % (durasi, args.orde))
    print()
    print('Rincian file .rmk:')
    for nama, ukuran in rincian.items():
        print('  %-12s %10d byte' % (nama, ukuran))
    print('  %-12s %10d byte' % ('TOTAL', len(isi)))
    print()
    print('Ukuran  : %d -> %d byte (%s dari asli)' % (n, len(isi), rmh.persen(len(isi), n)))
    if n:
        print('Laju    : %.2f MB/detik' % (n / durasi / 1e6))
        print()
        print('Byte berhasil ditebak di konteks orde:')
        for k in range(args.orde, -1, -1):
            print('  orde %2d : %8d byte (%5.1f%%)  dari %d konteks' % (
                k, model.statistik[k], model.statistik[k] / n * 100, model.jumlah_konteks()[k]))
        print('  orde -1 : %8d byte (%5.1f%%)  byte yang benar-benar baru' % (
            model.statistik[-1], model.statistik[-1] / n * 100))
        print()
        print('ESCAPE  : %d kali, tabel SEE %d kunci (dipelajari, tidak disimpan)' % (
            model.jumlah_escape, model.jumlah_see))

    if args.verifikasi:
        mulai = time.perf_counter()
        if decode(isi) != data:
            sys.exit('Verifikasi GAGAL: hasil decode berbeda dengan file asli')
        print('Verifikasi: decode ulang identik dengan file asli (%.3f detik)' % (time.perf_counter() - mulai))


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
    print('%-26s %12s %9s %10s' % ('Metode', 'Ukuran', '% asli', 'Detik'))

    def baris(nama, fungsi):
        mulai = time.perf_counter()
        ukuran = len(fungsi())
        print('%-26s %12d %9s %10.3f' % (nama, ukuran, rmh.persen(ukuran, n), time.perf_counter() - mulai))

    for k in args.orde:
        if args.python:
            baris('RMK2 orde %d (Python)' % k, lambda: rk2.encode(data, k)[0])
        baris('RMK2 orde %d (numba)' % k, lambda: encode(data, k)[0])
    baris('zlib -9', lambda: zlib.compress(data, 9))
    baris('lzma -9', lambda: lzma.compress(data, preset=9))


def main():
    parser = argparse.ArgumentParser(
        description='Return[er] Machine konteks versi 2 (.rmk RMK2), implementasi cepat dengan numba.')
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

    p = sub.add_parser('bandingkan', help='bandingkan RMK2 (numba), zlib, lzma (tanpa menulis file)')
    p.add_argument('input')
    p.add_argument('-k', '--orde', type=int, nargs='+', default=[3, 4, 5],
                   help='daftar orde yang dicoba (default: 3 4 5)')
    p.add_argument('--python', action='store_true', help='ikut jalankan versi Python (rmh_konteks2.py) sebagai pembanding')
    p.set_defaults(func=cmd_bandingkan)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
