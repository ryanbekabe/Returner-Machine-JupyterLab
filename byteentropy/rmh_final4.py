import os
import sys
import time
import zlib
import lzma
import hashlib
import argparse
from concurrent.futures import ThreadPoolExecutor

import rmh
import rmh_adaptif as ra
import rmh_konteks3 as rk3
import rmh_final as rf
import rmh_final2 as rf2
import rmh_final3 as rf3
# rmh_final4.py - Return[er] Machine Final versi CEPAT (format RMF3 yang sama)
# Sama dengan rmh_final3.py, tetapi konteks2 dikodekan dengan rmh_konteks3.py (numba,
# hasil identik dengan rmh_konteks2.py). Karena jauh lebih cepat, pemilihan mode tidak
# perlu lagi menebak dari sampel:
#   - konteks2 orde 1..6 diuji pada data PENUH, paralel di beberapa core;
#   - "campuran" (blok acak disimpan mentah) dibandingkan dengan "semua blok dikodekan
#     model" memakai ukuran sebenarnya pada data penuh, bukan sampel orde 3.
# File yang dihasilkan tetap format RMF3, jadi bisa dibuka oleh rmh_final3.py, dan
# rmh_final4.py bisa membuka RMF1, RMF2, dan RMF3.

MENTAH, ADAPTIF, KONTEKS2 = rf3.MENTAH, rf3.ADAPTIF, rf3.KONTEKS2
ORDE_PENUH = (1, 2, 3, 4, 5, 6)         # orde yang diuji pada data penuh
BATAS_UJI_SEMUA = 64 * 1024 * 1024      # di atas ini, campuran vs semua model memakai sampel
MEMORI_PARALEL = 2 * 1024 ** 3          # perkiraan batas memori untuk encode paralel
BYTE_PER_KONTEKS = 64                   # perkiraan memori per konteks (hash table + blok isi)


def nama_kandidat(mode, orde=None):
    return rf3.nama_kandidat(mode, orde)


def kodekan(data, mode, orde=None):
    if mode == KONTEKS2:
        return rk3.kodekan_konteks(data, orde)[0]
    return rf.kodekan(data, mode, orde)


def jumlah_pekerja(n, banyak, konteks_per_byte):
    # Setiap encode paralel butuh tabel konteks sendiri. Jumlah konteks diperkirakan dari
    # sampel jika ada; tanpa sampel dipakai batas atas (orde + 1) konteks per byte.
    per_tugas = max(1, int(n * konteks_per_byte * BYTE_PER_KONTEKS))
    return int(max(1, min(banyak, os.cpu_count() or 1, MEMORI_PARALEL // per_tugas)))


def uji_orde(data, daftar_orde, konteks_per_byte=None):
    # Kodekan data dengan beberapa orde konteks2 sekaligus (numba melepas GIL).
    # Mengembalikan daftar (orde, kode, detik, jumlah konteks).
    if konteks_per_byte is None:
        konteks_per_byte = max(daftar_orde) + 1

    def tugas(orde):
        mulai = time.perf_counter()
        kode, stat = rk3.kodekan_konteks(data, orde)
        return orde, kode, time.perf_counter() - mulai, sum(stat.jumlah_konteks())
    with ThreadPoolExecutor(jumlah_pekerja(len(data), len(daftar_orde), konteks_per_byte)) as ex:
        return list(ex.map(tugas, daftar_orde))


def pilih_mode(data, orde_paksa=None):
    # Mengembalikan (mode, orde, kode, info). Jika ukurannya sama, kandidat yang lebih
    # awal (lebih sederhana, orde lebih rendah) dipilih.
    hasil, penuh = [], []
    pakai_sampel = False
    if orde_paksa is not None:
        _, kode, detik, _ = uji_orde(data, [orde_paksa])[0]
        hasil.append((nama_kandidat(KONTEKS2, orde_paksa), len(data), len(kode), detik))
        mode, orde = KONTEKS2, orde_paksa
    else:
        terbaik = None
        pakai_sampel = len(data) > rf.BATAS_UJI_PENUH
        uji = rf.ambil_sampel(data) if pakai_sampel else data
        # adaptif masih Python: diuji pada sampel untuk file besar
        for m in (MENTAH, ADAPTIF):
            mulai = time.perf_counter()
            kode = kodekan(uji, m)
            hasil.append((nama_kandidat(m), len(uji), len(kode), time.perf_counter() - mulai))
            if terbaik is None or len(kode) < len(terbaik[2]):
                terbaik = (m, None, kode)
        if pakai_sampel:
            # bandingkan adaptif dengan konteks2 pada sampel yang sama
            konteks_per_byte = 0
            for o, kode, detik, n_konteks in uji_orde(uji, ORDE_PENUH):
                hasil.append((nama_kandidat(KONTEKS2, o), len(uji), len(kode), detik))
                konteks_per_byte = max(konteks_per_byte, n_konteks / len(uji))
                if len(kode) < len(terbaik[2]):
                    terbaik = (KONTEKS2, o, kode)
            mode, orde, kode = terbaik
            if mode == KONTEKS2:
                # orde terbaik dicari ulang pada data penuh (sampel cenderung memilih orde rendah)
                kode = None
                for o, k, detik, _ in uji_orde(data, ORDE_PENUH, konteks_per_byte):
                    penuh.append((nama_kandidat(KONTEKS2, o), len(k), detik))
                    if kode is None or len(k) < len(kode):
                        orde, kode = o, k
            else:
                mulai = time.perf_counter()
                kode = kodekan(data, mode)
                penuh.append((nama_kandidat(mode), len(kode), time.perf_counter() - mulai))
        else:
            for o, kode, detik, _ in uji_orde(data, ORDE_PENUH):
                hasil.append((nama_kandidat(KONTEKS2, o), len(data), len(kode), detik))
                if len(kode) < len(terbaik[2]):
                    terbaik = (KONTEKS2, o, kode)
            mode, orde, kode = terbaik
    if mode != MENTAH and len(kode) >= len(data):
        # hasil pada data penuh ternyata tidak lebih kecil: simpan mentah
        mode, orde, kode = MENTAH, None, bytes(data)
    return mode, orde, kode, {'uji': hasil, 'sampel': pakai_sampel, 'penuh': penuh}


def susun(data, sha, ukuran_blok, peta, blok, mode, orde, kode):
    bagian_mentah = b''.join(b for b, m in zip(blok, peta) if not m)
    header = rf3.MAGIC + rmh.tulis_varint(len(data)) + sha + rmh.tulis_varint(ukuran_blok)
    header += rf2.kode_peta(peta) + bytes([mode])
    if mode == ADAPTIF:
        header += rmh.tulis_varint(ra.TAMBAH_DEFAULT) + rmh.tulis_varint(ra.BATAS_DEFAULT)
    elif mode == KONTEKS2:
        header += bytes([orde])
    header += rmh.tulis_varint(len(kode))
    return header + kode + bagian_mentah, len(header), len(bagian_mentah)


def encode(data, ukuran_blok=rf3.BLOK_DEFAULT, ambang=rf3.AMBANG_DEFAULT, orde_paksa=None, uji_semua=True):
    if ukuran_blok < 1:
        raise ValueError('Ukuran blok minimal 1 byte')
    if orde_paksa is not None and not 0 <= orde_paksa <= rk3.ORDE_MAKS:
        raise ValueError('Orde harus di antara 0 dan %d' % rk3.ORDE_MAKS)
    sha = hashlib.sha256(data).digest()
    blok, peta = rf2.bagi(data, ukuran_blok, ambang)
    campuran = not all(peta) and any(peta)

    bagian_model = b''.join(b for b, m in zip(blok, peta) if m)
    if bagian_model:
        mode, orde, kode, info = pilih_mode(bagian_model, orde_paksa)
    else:
        mode, orde, kode, info = MENTAH, None, b'', {'uji': [], 'sampel': False, 'penuh': []}
    isi, panjang_header, byte_mentah = susun(data, sha, ukuran_blok, peta, blok, mode, orde, kode)

    uji_campuran = None
    if campuran and uji_semua and len(data) <= BATAS_UJI_SEMUA:
        # Entropy orde-0 tinggi belum tentu berarti tidak bisa diperkecil. Coba juga
        # "semua blok dikodekan model" pada data penuh, dengan orde terpilih (atau 3 jika
        # bagian berpola tidak memakai konteks2) dan orde berikutnya, lalu ambil yang terkecil.
        o = orde if mode == KONTEKS2 else 3
        daftar = [o] if orde_paksa is not None else sorted({o, min(o + 1, rk3.ORDE_MAKS)})
        semua_peta = [True] * len(peta)
        terbaik = None
        for o2, kode2, _, _ in uji_orde(data, daftar):
            if terbaik is None or len(kode2) < len(terbaik[1]):
                terbaik = (o2, kode2)
        isi2, header2, _ = susun(data, sha, ukuran_blok, semua_peta, blok, KONTEKS2, terbaik[0], terbaik[1])
        uji_campuran = {'campuran': len(isi), 'semua': len(isi2), 'orde_semua': terbaik[0], 'byte_uji': len(data)}
        if len(isi2) < len(isi):
            isi, panjang_header, byte_mentah = isi2, header2, 0
            peta, mode, orde, kode = semua_peta, KONTEKS2, terbaik[0], terbaik[1]
            bagian_model = data
    elif campuran and uji_semua:
        # file sangat besar: keputusan dari sampel seperti rmh_final3.py
        peta_baru, uji_campuran = rf3.uji_peta(blok, peta)
        if all(peta_baru):
            peta = peta_baru
            bagian_model = data
            mode, orde, kode, info = pilih_mode(data, orde_paksa)
            isi, panjang_header, byte_mentah = susun(data, sha, ukuran_blok, peta, blok, mode, orde, kode)

    info.update({
        'mode': mode, 'orde': orde, 'blok': len(blok), 'blok_model': sum(peta),
        'byte_model': len(bagian_model), 'byte_mentah': byte_mentah, 'kode_model': len(kode),
        'header': panjang_header, 'uji_campuran': uji_campuran,
    })
    return isi, info


def decode(isi):
    if isi[:4] in (rf.MAGIC, rf2.MAGIC):
        return rf2.decode(isi)      # file .rmf versi 1 atau 2
    h = rf3.baca_rmf3(isi)
    if h['mode'] != KONTEKS2 or not h['byte_model']:
        return rf3.decode(isi)      # mentah / adaptif / konteks RMK1: jalur Python
    model = rk3.dekode_konteks(h['kode'], h['byte_model'], h['param']['orde'])
    hasil = bytearray()
    i_model = i_mentah = 0
    for p, m in zip(h['panjang'], h['peta']):
        if m:
            hasil += model[i_model:i_model + p]
            i_model += p
        else:
            hasil += h['mentah'][i_mentah:i_mentah + p]
            i_mentah += p
    if hashlib.sha256(hasil).digest() != h['sha']:
        raise ValueError('SHA-256 tidak cocok, hasil decode rusak')
    return bytes(hasil)


# ---------- perintah ----------

def cmd_encode(args):
    data = rmh.baca_file(args.input)
    output = args.output or args.input + '.rmf'
    mulai = time.perf_counter()
    try:
        isi, info = encode(data, args.blok, args.ambang, args.orde, not args.tanpa_uji_semua)
    except ValueError as e:
        sys.exit('Encode gagal: %s' % e)
    durasi = time.perf_counter() - mulai

    if not args.tanpa_verifikasi:
        mulai_v = time.perf_counter()
        if decode(isi) != data:
            sys.exit('Verifikasi GAGAL: hasil decode tidak sama dengan file asli. File tidak ditulis.')
        durasi_v = time.perf_counter() - mulai_v
    rmh.tulis_file(output, isi)

    n = len(data)
    print('Pembagian blok (%d byte, ambang entropy %.2f bit/byte):' % (args.blok, args.ambang))
    print('  %-26s %8d blok  %10d byte' % ('dikodekan model', info['blok_model'], info['byte_model']))
    print('  %-26s %8d blok  %10d byte' % ('disimpan mentah', info['blok'] - info['blok_model'], info['byte_mentah']))
    u = info['uji_campuran']
    if u and 'orde_semua' in u:
        print('  uji pada data penuh: campuran %d byte, semua model (konteks2 orde %d) %d byte -> %s' % (
            u['campuran'], u['orde_semua'], u['semua'], 'semua model' if u['semua'] < u['campuran'] else 'campuran'))
    elif u:
        print('  uji pada sampel %d byte (konteks2 orde %d): campuran %d byte, semua model %d byte -> %s' % (
            u['byte_uji'], rf3.ORDE_UJI_PETA, u['campuran'], u['semua'],
            'semua model' if u['semua'] < u['campuran'] else 'campuran'))
    print()
    if info['uji']:
        print('Pemilihan mode untuk bagian berpola (%s):' % (
            'sampel %d byte' % info['uji'][0][1] if info['sampel'] else 'data penuh'))
        for nama, ukuran_uji, ukuran, detik in info['uji']:
            print('  %-18s %12d %8.1f%% %9.3f detik' % (nama, ukuran, ukuran / ukuran_uji * 100, detik))
        for nama, ukuran, detik in info['penuh']:
            print('  %-18s %12d  (bagian berpola penuh) %7.3f detik' % (nama, ukuran, detik))
        print()
    print('Encode     :', args.input, '->', output, '(%.3f detik)' % durasi)
    print('Mode model :', nama_kandidat(info['mode'], info['orde']))
    print('SHA-256    :', hashlib.sha256(data).hexdigest())
    print('Rincian    : header %d + kode model %d + blok mentah %d byte' % (
        info['header'], info['kode_model'], info['byte_mentah']))
    print('Ukuran     : %d -> %d byte (%s dari asli)' % (n, len(isi), rmh.persen(len(isi), n)))
    if args.tanpa_verifikasi:
        print('Verifikasi : dilewati')
    else:
        print('Verifikasi : decode identik, SHA-256 cocok (%.3f detik)' % durasi_v)


def cmd_decode(args):
    isi = rmh.baca_file(args.input)
    if args.output:
        output = args.output
    elif args.input.endswith('.rmf'):
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
    print('Ukuran  :', len(data), 'byte')
    print('SHA-256 :', hashlib.sha256(data).hexdigest(), '(cocok)')


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

    if args.python:
        baris('.rmf versi 3 (Python)', lambda: rf3.encode(data)[0])
    baris('.rmf versi 3 (rmh_final4)', lambda: encode(data)[0])
    baris('zlib -9 (zip)', lambda: zlib.compress(data, 9))
    baris('lzma -9e (7z)', lambda: lzma.compress(data, preset=9 | lzma.PRESET_EXTREME))


def main():
    parser = argparse.ArgumentParser(
        description='Return[er] Machine Final v4: versi cepat (numba) dari rmh_final3.py, format RMF3 (.rmf).')
    sub = parser.add_subparsers(dest='perintah', required=True)

    p = sub.add_parser('encode', help='file asli -> file .rmf (format RMF3)')
    p.add_argument('input')
    p.add_argument('-o', '--output', help='nama file .rmf (default: <input>.rmf)')
    p.add_argument('-b', '--blok', type=int, default=rf3.BLOK_DEFAULT,
                   help='ukuran blok dalam byte (default: %d)' % rf3.BLOK_DEFAULT)
    p.add_argument('-a', '--ambang', type=float, default=rf3.AMBANG_DEFAULT,
                   help='blok dengan entropy di atas ambang disimpan mentah (default: %.1f bit/byte, 8 = semua dikodekan)' % rf3.AMBANG_DEFAULT)
    p.add_argument('-k', '--orde', type=int, choices=range(0, rk3.ORDE_MAKS + 1), metavar='0..%d' % rk3.ORDE_MAKS,
                   help='paksa mode konteks2 dengan orde ini')
    p.add_argument('--tanpa-uji-semua', action='store_true',
                   help='selalu simpan blok acak secara mentah (encode dan decode jauh lebih cepat, hasil bisa sedikit lebih besar)')
    p.add_argument('--tanpa-verifikasi', action='store_true', help='jangan decode ulang setelah encode')
    p.set_defaults(func=cmd_encode)

    p = sub.add_parser('decode', help='file .rmf (versi 1, 2, atau 3) -> file asli')
    p.add_argument('input')
    p.add_argument('-o', '--output', help='nama file hasil (default: <input tanpa .rmf>.decoded)')
    p.set_defaults(func=cmd_decode)

    p = sub.add_parser('info', help='tampilkan header dan peta blok tanpa decode')
    p.add_argument('input')
    p.add_argument('--semua', action='store_true', help='tampilkan seluruh peta blok')
    p.set_defaults(func=rf3.cmd_info)

    p = sub.add_parser('bandingkan', help='bandingkan .rmf, zip, dan 7z (tanpa menulis file)')
    p.add_argument('input')
    p.add_argument('--python', action='store_true', help='ikut jalankan rmh_final3.py (lambat) sebagai pembanding')
    p.set_defaults(func=cmd_bandingkan)

    args = parser.parse_args()
    if args.perintah == 'encode' and not 0 <= args.ambang <= 8:
        sys.exit('Ambang harus di antara 0 dan 8')
    args.func(args)


if __name__ == '__main__':
    main()
