import sys
import math
import time
import hashlib
import argparse
from collections import Counter

import rmh
import rmh_adaptif as ra
import rmh_konteks as rk
import rmh_final as rf
# rmh_final2.py - Return[er] Machine Final, format RMF2 (mode campuran per blok)
# Lanjutan rmh_final.py. File dibagi menjadi blok kecil (default 1.024 byte):
#   - blok yang sudah acak / sudah terkompresi (entropy orde-0 di atas ambang)
#     disimpan MENTAH tanpa diproses model: tidak membengkak dan sangat cepat;
#   - blok lainnya digabung menjadi satu aliran dan dikodekan dengan mode terbaik
#     (dipilih oleh rmh_final.py: konteks orde 1..5, adaptif, atau mentah).
#     Karena digabung, model tetap belajar dari semua blok berpola sepanjang file.
# Contoh: PDF berisi gambar JPEG/Flate + struktur teks. Gambar disalin mentah,
# hanya struktur teks yang dikodekan.
#
# Format file .rmf versi 2 (varint = LEB128):
#   [4 byte ] magic "RMF2"
#   [varint ] n            : ukuran file asli (byte)
#   [32 byte] SHA-256 file asli
#   [varint ] B            : ukuran blok (byte)
#   [m byte ] peta blok    : 1 bit per blok (1 = model, 0 = mentah), m = ceil(jumlah blok / 8)
#   [1 byte ] mode model   : 0 = mentah, 1 = adaptif, 2 = konteks
#   parameter mode (sama dengan RMF1): adaptif = varint tambah, varint batas; konteks = 1 byte orde
#   [varint ] panjang kode model
#   [k byte ] kode model   : aliran gabungan blok berpola
#   [sisa   ] blok mentah, berurutan

MAGIC = b'RMF2'
BLOK_DEFAULT = 1024
AMBANG_DEFAULT = 7.6


def entropy(blok):
    n = len(blok)
    return -sum(c / n * math.log2(c / n) for c in Counter(blok).values()) + 0.0


def bagi(data, ukuran_blok, ambang):
    # True = blok dikodekan model, False = disimpan mentah
    blok = [data[i:i + ukuran_blok] for i in range(0, len(data), ukuran_blok)]
    return blok, [entropy(b) <= ambang for b in blok]


def uji_peta(blok, peta):
    # Entropy orde-0 tinggi belum tentu berarti tidak bisa diperkecil: model konteks
    # masih bisa menemukan pola (misalnya PNG). Bandingkan "campuran" dengan
    # "semua blok dikodekan model" memakai konteks orde 3, pada semua blok jika
    # file kecil, atau pada blok di awal, tengah, dan akhir file jika file besar.
    if not blok or all(peta):
        return peta, None
    total = sum(len(b) for b in blok)
    if total <= rf.BATAS_UJI_PENUH:
        indeks = list(range(len(blok)))
    else:
        k = max(1, rf.UKURAN_SAMPEL // len(blok[0]))
        tengah = (len(blok) - k) // 2
        indeks = sorted(set(range(k)) | set(range(tengah, tengah + k)) | set(range(len(blok) - k, len(blok))))
    model = b''.join(blok[i] for i in indeks if peta[i])
    mentah = sum(len(blok[i]) for i in indeks if not peta[i])
    campuran = (len(rk.kodekan_konteks(model, 3)[0]) if model else 0) + mentah
    semua = len(rk.kodekan_konteks(b''.join(blok[i] for i in indeks), 3)[0])
    hasil = {'campuran': campuran, 'semua': semua, 'byte_uji': sum(len(blok[i]) for i in indeks)}
    if semua < campuran:
        return [True] * len(peta), hasil
    return peta, hasil


def kode_peta(peta):
    hasil = bytearray((len(peta) + 7) // 8)
    for i, model in enumerate(peta):
        if model:
            hasil[i >> 3] |= 0x80 >> (i & 7)
    return bytes(hasil)


def baca_peta(isi, jumlah):
    return [bool(isi[i >> 3] & (0x80 >> (i & 7))) for i in range(jumlah)]


# ---------- encode / decode ----------

def encode(data, ukuran_blok=BLOK_DEFAULT, ambang=AMBANG_DEFAULT, orde_paksa=None):
    if ukuran_blok < 1:
        raise ValueError('Ukuran blok minimal 1 byte')
    sha = hashlib.sha256(data).digest()
    blok, peta = bagi(data, ukuran_blok, ambang)
    peta, uji_campuran = uji_peta(blok, peta)
    bagian_model = b''.join(b for b, m in zip(blok, peta) if m)
    bagian_mentah = b''.join(b for b, m in zip(blok, peta) if not m)

    # aliran model dikodekan dengan pemilihan mode dari rmh_final.py
    if bagian_model:
        isi_dalam, info = rf.encode(bagian_model, orde_paksa)
        mode, _, _, param, pos = rf.baca_rmf(isi_dalam)
        kode = isi_dalam[pos:]
    else:
        mode, param, kode, info = rf.MENTAH, {}, b'', {'mode': rf.MENTAH, 'orde': None, 'uji': [], 'sampel': False, 'penuh': []}

    header = MAGIC + rmh.tulis_varint(len(data)) + sha + rmh.tulis_varint(ukuran_blok)
    header += kode_peta(peta) + bytes([mode])
    if mode == rf.ADAPTIF:
        header += rmh.tulis_varint(param['tambah']) + rmh.tulis_varint(param['batas'])
    elif mode == rf.KONTEKS:
        header += bytes([param['orde']])
    header += rmh.tulis_varint(len(kode))

    info.update({
        'blok': len(blok), 'blok_model': sum(peta), 'byte_model': len(bagian_model),
        'byte_mentah': len(bagian_mentah), 'kode_model': len(kode), 'header': len(header),
        'uji_campuran': uji_campuran,
    })
    return header + kode + bagian_mentah, info


def baca_rmf2(isi):
    if isi[:4] != MAGIC:
        raise ValueError('Bukan file .rmf versi 2 (magic tidak cocok)')
    try:
        n, pos = rmh.baca_varint(isi, 4)
        if pos + 32 > len(isi):
            raise ValueError
        sha = isi[pos:pos + 32]
        ukuran_blok, pos = rmh.baca_varint(isi, pos + 32)
        if ukuran_blok < 1:
            raise ValueError
        jumlah = (n + ukuran_blok - 1) // ukuran_blok
        m = (jumlah + 7) // 8
        if pos + m + 1 > len(isi):
            raise ValueError
        peta = baca_peta(isi[pos:pos + m], jumlah)
        pos += m
        mode = isi[pos]
        pos += 1
        param = {}
        if mode == rf.ADAPTIF:
            param['tambah'], pos = rmh.baca_varint(isi, pos)
            param['batas'], pos = rmh.baca_varint(isi, pos)
        elif mode == rf.KONTEKS:
            if pos >= len(isi):
                raise ValueError
            param['orde'] = isi[pos]
            pos += 1
        elif mode != rf.MENTAH:
            raise ValueError('Mode tidak dikenal: %d' % mode)
        panjang_kode, pos = rmh.baca_varint(isi, pos)
    except ValueError as e:
        raise ValueError(str(e) if str(e) else 'File .rmf terpotong (header tidak lengkap)')
    if mode == rf.KONTEKS and param['orde'] > rk.ORDE_MAKS:
        raise ValueError('Orde tidak valid: %d' % param['orde'])
    if mode == rf.ADAPTIF and not (1 <= param['tambah'] <= 1 << 16 and 512 <= param['batas'] <= 1 << 24):
        raise ValueError('Parameter adaptif tidak valid')

    panjang = [min(ukuran_blok, n - i * ukuran_blok) for i in range(jumlah)]
    byte_model = sum(p for p, m in zip(panjang, peta) if m)
    byte_mentah = n - byte_model
    if len(isi) - pos != panjang_kode + byte_mentah:
        raise ValueError('Ukuran isi tidak sesuai (diharapkan %d byte, ada %d)' % (panjang_kode + byte_mentah, len(isi) - pos))
    return {'n': n, 'sha': sha, 'blok': ukuran_blok, 'peta': peta, 'panjang': panjang, 'mode': mode,
            'param': param, 'byte_model': byte_model, 'byte_mentah': byte_mentah,
            'kode': isi[pos:pos + panjang_kode], 'mentah': isi[pos + panjang_kode:], 'header': pos}


def decode(isi):
    if isi[:4] == rf.MAGIC:
        return rf.decode(isi)       # file .rmf versi 1
    h = baca_rmf2(isi)
    kode, n_model = h['kode'], h['byte_model']
    if h['mode'] == rf.MENTAH:
        if len(kode) != n_model:
            raise ValueError('Panjang data model mentah tidak sesuai')
        model = bytes(kode)
    elif not n_model:
        model = b''
    elif h['mode'] == rf.ADAPTIF:
        model = ra.dekode_aritmetika(kode, n_model, h['param']['tambah'], h['param']['batas'])
    else:
        model = rk.dekode_konteks(kode, n_model, h['param']['orde'])

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
        isi, info = encode(data, args.blok, args.ambang, args.orde)
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
    print('  %-26s %8d blok  %10d byte' % ('dikodekan model (berpola)', info['blok_model'], info['byte_model']))
    print('  %-26s %8d blok  %10d byte' % ('disimpan mentah', info['blok'] - info['blok_model'], info['byte_mentah']))
    u = info['uji_campuran']
    if u:
        print('  uji pada %d byte (konteks orde 3): campuran %d byte, semua model %d byte -> %s' % (
            u['byte_uji'], u['campuran'], u['semua'], 'semua model' if u['semua'] < u['campuran'] else 'campuran'))
    print()
    if info['uji']:
        print('Pemilihan mode untuk bagian berpola (%s):' % (
            'sampel %d byte' % info['uji'][0][1] if info['sampel'] else 'penuh'))
        for nama, ukuran_uji, ukuran, detik in info['uji']:
            print('  %-18s %12d %8.1f%% %9.3f detik' % (nama, ukuran, ukuran / ukuran_uji * 100, detik))
        for nama, ukuran, detik in info['penuh']:
            print('  %-18s %12d  (bagian berpola penuh) %7.3f detik' % (nama, ukuran, detik))
        print()
    print('Encode     :', args.input, '->', output, '(%.3f detik)' % durasi)
    print('Mode model :', rf.nama_kandidat(info['mode'], info['orde']))
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
    print('Decode  :', args.input, '->', output, '(%.3f detik)' % durasi)
    print('Ukuran  :', len(data), 'byte')
    print('SHA-256 :', hashlib.sha256(data).hexdigest(), '(cocok)')


def cmd_info(args):
    isi = rmh.baca_file(args.input)
    if isi[:4] == rf.MAGIC:
        print('Format versi 1 (RMF1):')
        rf.cmd_info(args)
        return
    try:
        h = baca_rmf2(isi)
    except ValueError as e:
        sys.exit('File tidak valid: %s' % e)
    jumlah_model = sum(h['peta'])
    print('File .rmf        :', args.input, '(%d byte, format RMF2)' % len(isi))
    print('Ukuran file asli :', h['n'], 'byte')
    print('SHA-256 asli     :', h['sha'].hex())
    print('Ukuran blok      :', h['blok'], 'byte')
    print('Blok model       : %d blok, %d byte -> kode %d byte (%s)' % (
        jumlah_model, h['byte_model'], len(h['kode']), rf.nama_kandidat(h['mode'], h['param'].get('orde'))))
    print('Blok mentah      : %d blok, %d byte' % (len(h['peta']) - jumlah_model, h['byte_mentah']))
    print('Header           :', h['header'], 'byte (termasuk peta blok)')
    print('Rasio            :', rmh.persen(len(isi), h['n']))
    if h['peta']:
        lebar = 64
        print()
        print('Peta blok (M = model, . = mentah, %d blok per baris):' % lebar)
        baris = ''.join('M' if m else '.' for m in h['peta'])
        tampil = range(0, len(baris), lebar)
        if len(tampil) > 24 and not args.semua:
            tampil = list(tampil[:16]) + [None] + list(tampil[-4:])
        for i in tampil:
            print('  ...' if i is None else '  %8d  %s' % (i, baris[i:i + lebar]))


def main():
    parser = argparse.ArgumentParser(description='Return[er] Machine Final v2: mode campuran per blok + SHA-256 (.rmf).')
    sub = parser.add_subparsers(dest='perintah', required=True)

    p = sub.add_parser('encode', help='file asli -> file .rmf versi 2')
    p.add_argument('input')
    p.add_argument('-o', '--output', help='nama file .rmf (default: <input>.rmf)')
    p.add_argument('-b', '--blok', type=int, default=BLOK_DEFAULT,
                   help='ukuran blok dalam byte (default: %d)' % BLOK_DEFAULT)
    p.add_argument('-a', '--ambang', type=float, default=AMBANG_DEFAULT,
                   help='blok dengan entropy di atas ambang disimpan mentah (default: %.1f bit/byte, 8 = semua dikodekan)' % AMBANG_DEFAULT)
    p.add_argument('-k', '--orde', type=int, choices=range(0, rk.ORDE_MAKS + 1), metavar='0..%d' % rk.ORDE_MAKS,
                   help='paksa mode konteks dengan orde ini untuk bagian berpola')
    p.add_argument('--tanpa-verifikasi', action='store_true', help='jangan decode ulang setelah encode')
    p.set_defaults(func=cmd_encode)

    p = sub.add_parser('decode', help='file .rmf (versi 1 atau 2) -> file asli')
    p.add_argument('input')
    p.add_argument('-o', '--output', help='nama file hasil (default: <input tanpa .rmf>.decoded)')
    p.set_defaults(func=cmd_decode)

    p = sub.add_parser('info', help='tampilkan header dan peta blok tanpa decode')
    p.add_argument('input')
    p.add_argument('--semua', action='store_true', help='tampilkan seluruh peta blok')
    p.set_defaults(func=cmd_info)

    args = parser.parse_args()
    if args.perintah == 'encode' and not 0 <= args.ambang <= 8:
        sys.exit('Ambang harus di antara 0 dan 8')
    args.func(args)


if __name__ == '__main__':
    main()
