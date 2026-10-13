import sys
import time
import zlib
import lzma
import hashlib
import argparse

import rmh
import rmh_adaptif as ra
import rmh_konteks as rk
import rmh_konteks2 as rk2
import rmh_final as rf
import rmh_final2 as rf2
# rmh_final3.py - Return[er] Machine Final, format RMF3
# Sama dengan rmh_final2.py (mode campuran per blok + SHA-256), tetapi bagian
# berpola dikodekan dengan konteks versi 2 (rmh_konteks2.py: PPM + SEE + update
# exclusion), yang 7-23% lebih kecil dari konteks versi 1.
#   - blok yang sudah acak / sudah terkompresi disimpan MENTAH;
#   - blok lainnya digabung menjadi satu aliran dan dikodekan dengan mode terbaik:
#     konteks2 orde 1..5 (orde 6 dicoba jika orde 5 yang terbaik), adaptif, atau mentah.
#
# Format file .rmf versi 3 (varint = LEB128), sama dengan RMF2 kecuali magic dan mode:
#   [4 byte ] magic "RMF3"
#   [varint ] n            : ukuran file asli (byte)
#   [32 byte] SHA-256 file asli
#   [varint ] B            : ukuran blok (byte)
#   [m byte ] peta blok    : 1 bit per blok (1 = model, 0 = mentah), m = ceil(jumlah blok / 8)
#   [1 byte ] mode model   : 0 = mentah, 1 = adaptif, 2 = konteks (RMK1), 3 = konteks2 (RMK2)
#   parameter mode: adaptif = varint tambah, varint batas; konteks / konteks2 = 1 byte orde
#   [varint ] panjang kode model
#   [k byte ] kode model   : aliran gabungan blok berpola
#   [sisa   ] blok mentah, berurutan
# decode juga bisa membuka RMF1 dan RMF2.

MAGIC = b'RMF3'
MENTAH, ADAPTIF, KONTEKS, KONTEKS2 = rf.MENTAH, rf.ADAPTIF, rf.KONTEKS, 3
NAMA_MODE = {MENTAH: 'mentah', ADAPTIF: 'adaptif', KONTEKS: 'konteks', KONTEKS2: 'konteks2'}
ORDE_KANDIDAT = (1, 2, 3, 4, 5)
ORDE_UJI_PETA = 3
BLOK_DEFAULT = rf2.BLOK_DEFAULT
AMBANG_DEFAULT = rf2.AMBANG_DEFAULT


# ---------- pemilihan mode ----------

def nama_kandidat(mode, orde=None):
    return '%s orde %d' % (NAMA_MODE[mode], orde) if mode in (KONTEKS, KONTEKS2) else NAMA_MODE[mode]


def kodekan(data, mode, orde=None):
    if mode == KONTEKS2:
        return rk2.kodekan_konteks(data, orde)[0]
    return rf.kodekan(data, mode, orde)


def pilih_mode(data, orde_paksa=None):
    # Mengembalikan (mode, orde, kode, info). Kandidat diuji berurutan; jika ukurannya
    # sama, yang lebih awal (lebih sederhana) dipilih. File besar diuji memakai sampel
    # 3 x 64 KB (awal, tengah, akhir), lalu dikodekan ulang penuh.
    if orde_paksa is not None:
        kandidat = [(KONTEKS2, orde_paksa)]
    else:
        kandidat = [(MENTAH, None), (ADAPTIF, None)] + [(KONTEKS2, k) for k in ORDE_KANDIDAT]
    pakai_sampel = len(data) > rf.BATAS_UJI_PENUH and orde_paksa is None
    uji = rf.ambil_sampel(data) if pakai_sampel else data

    hasil = []
    terbaik = None
    for mode, orde in kandidat:
        mulai = time.perf_counter()
        kode = kodekan(uji, mode, orde)
        hasil.append((nama_kandidat(mode, orde), len(uji), len(kode), time.perf_counter() - mulai))
        if terbaik is None or len(kode) < len(terbaik[2]):
            terbaik = (mode, orde, kode)
    mode, orde, kode = terbaik

    penuh = []
    if pakai_sampel:
        mulai = time.perf_counter()
        kode = kodekan(data, mode, orde)
        penuh.append((nama_kandidat(mode, orde), len(kode), time.perf_counter() - mulai))
    # Konteks panjang butuh data banyak untuk dipelajari, jadi sampel (dan kandidat 1..5)
    # cenderung memilih orde terlalu rendah. Pada data penuh, naikkan orde selama mengecil.
    if mode == KONTEKS2 and orde_paksa is None and (pakai_sampel or orde == max(ORDE_KANDIDAT)):
        while orde < rk2.ORDE_MAKS:
            mulai = time.perf_counter()
            kode_lain = kodekan(data, KONTEKS2, orde + 1)
            penuh.append((nama_kandidat(KONTEKS2, orde + 1), len(kode_lain), time.perf_counter() - mulai))
            if len(kode_lain) >= len(kode):
                break
            kode, orde = kode_lain, orde + 1
    if mode != MENTAH and len(kode) >= len(data):
        # hasil pada data penuh ternyata tidak lebih kecil: simpan mentah
        mode, orde, kode = MENTAH, None, bytes(data)
    return mode, orde, kode, {'uji': hasil, 'sampel': pakai_sampel, 'penuh': penuh}


def uji_peta(blok, peta):
    # Sama dengan rmh_final2.uji_peta, tetapi memakai konteks versi 2: bandingkan
    # "campuran" dengan "semua blok dikodekan model" pada semua blok (file kecil)
    # atau pada blok di awal, tengah, dan akhir file (file besar).
    if not blok or all(peta):
        return peta, None
    if sum(len(b) for b in blok) <= rf.BATAS_UJI_PENUH:
        indeks = list(range(len(blok)))
    else:
        k = max(1, rf.UKURAN_SAMPEL // len(blok[0]))
        tengah = (len(blok) - k) // 2
        indeks = sorted(set(range(k)) | set(range(tengah, tengah + k)) | set(range(len(blok) - k, len(blok))))
    model = b''.join(blok[i] for i in indeks if peta[i])
    mentah = sum(len(blok[i]) for i in indeks if not peta[i])
    campuran = (len(rk2.kodekan_konteks(model, ORDE_UJI_PETA)[0]) if model else 0) + mentah
    semua = len(rk2.kodekan_konteks(b''.join(blok[i] for i in indeks), ORDE_UJI_PETA)[0])
    hasil = {'campuran': campuran, 'semua': semua, 'byte_uji': sum(len(blok[i]) for i in indeks)}
    if semua < campuran:
        return [True] * len(peta), hasil
    return peta, hasil


# ---------- encode / decode ----------

def encode(data, ukuran_blok=BLOK_DEFAULT, ambang=AMBANG_DEFAULT, orde_paksa=None):
    if ukuran_blok < 1:
        raise ValueError('Ukuran blok minimal 1 byte')
    if orde_paksa is not None and not 0 <= orde_paksa <= rk2.ORDE_MAKS:
        raise ValueError('Orde harus di antara 0 dan %d' % rk2.ORDE_MAKS)
    sha = hashlib.sha256(data).digest()
    blok, peta = rf2.bagi(data, ukuran_blok, ambang)
    peta, uji_campuran = uji_peta(blok, peta)
    bagian_model = b''.join(b for b, m in zip(blok, peta) if m)
    bagian_mentah = b''.join(b for b, m in zip(blok, peta) if not m)

    if bagian_model:
        mode, orde, kode, info = pilih_mode(bagian_model, orde_paksa)
    else:
        mode, orde, kode, info = MENTAH, None, b'', {'uji': [], 'sampel': False, 'penuh': []}

    header = MAGIC + rmh.tulis_varint(len(data)) + sha + rmh.tulis_varint(ukuran_blok)
    header += rf2.kode_peta(peta) + bytes([mode])
    if mode == ADAPTIF:
        header += rmh.tulis_varint(ra.TAMBAH_DEFAULT) + rmh.tulis_varint(ra.BATAS_DEFAULT)
    elif mode == KONTEKS2:
        header += bytes([orde])
    header += rmh.tulis_varint(len(kode))

    info.update({
        'mode': mode, 'orde': orde, 'blok': len(blok), 'blok_model': sum(peta),
        'byte_model': len(bagian_model), 'byte_mentah': len(bagian_mentah), 'kode_model': len(kode),
        'header': len(header), 'uji_campuran': uji_campuran,
    })
    return header + kode + bagian_mentah, info


def baca_rmf3(isi):
    # Tata letak RMF3 sama dengan RMF2; hanya magic dan mode konteks2 yang baru.
    if isi[:4] != MAGIC:
        raise ValueError('Bukan file .rmf versi 3 (magic tidak cocok)')
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
        peta = rf2.baca_peta(isi[pos:pos + m], jumlah)
        pos += m
        mode = isi[pos]
        pos += 1
        param = {}
        if mode == ADAPTIF:
            param['tambah'], pos = rmh.baca_varint(isi, pos)
            param['batas'], pos = rmh.baca_varint(isi, pos)
        elif mode in (KONTEKS, KONTEKS2):
            if pos >= len(isi):
                raise ValueError
            param['orde'] = isi[pos]
            pos += 1
        elif mode != MENTAH:
            raise ValueError('Mode tidak dikenal: %d' % mode)
        panjang_kode, pos = rmh.baca_varint(isi, pos)
    except ValueError as e:
        raise ValueError(str(e) if str(e) else 'File .rmf terpotong (header tidak lengkap)')
    if mode in (KONTEKS, KONTEKS2) and param['orde'] > rk2.ORDE_MAKS:
        raise ValueError('Orde tidak valid: %d' % param['orde'])
    if mode == ADAPTIF and not (1 <= param['tambah'] <= 1 << 16 and 512 <= param['batas'] <= 1 << 24):
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
    if isi[:4] in (rf.MAGIC, rf2.MAGIC):
        return rf2.decode(isi)      # file .rmf versi 1 atau 2
    h = baca_rmf3(isi)
    kode, n_model = h['kode'], h['byte_model']
    if h['mode'] == MENTAH:
        if len(kode) != n_model:
            raise ValueError('Panjang data model mentah tidak sesuai')
        model = bytes(kode)
    elif not n_model:
        model = b''
    elif h['mode'] == ADAPTIF:
        model = ra.dekode_aritmetika(kode, n_model, h['param']['tambah'], h['param']['batas'])
    elif h['mode'] == KONTEKS:
        model = rk.dekode_konteks(kode, n_model, h['param']['orde'])
    else:
        model = rk2.dekode_konteks(kode, n_model, h['param']['orde'])

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
        print('  uji pada %d byte (konteks2 orde %d): campuran %d byte, semua model %d byte -> %s' % (
            u['byte_uji'], ORDE_UJI_PETA, u['campuran'], u['semua'],
            'semua model' if u['semua'] < u['campuran'] else 'campuran'))
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


def cmd_info(args):
    isi = rmh.baca_file(args.input)
    if isi[:4] in (rf.MAGIC, rf2.MAGIC):
        rf2.cmd_info(args)
        return
    try:
        h = baca_rmf3(isi)
    except ValueError as e:
        sys.exit('File tidak valid: %s' % e)
    jumlah_model = sum(h['peta'])
    print('File .rmf        :', args.input, '(%d byte, format RMF3)' % len(isi))
    print('Ukuran file asli :', h['n'], 'byte')
    print('SHA-256 asli     :', h['sha'].hex())
    print('Ukuran blok      :', h['blok'], 'byte')
    print('Blok model       : %d blok, %d byte -> kode %d byte (%s)' % (
        jumlah_model, h['byte_model'], len(h['kode']), nama_kandidat(h['mode'], h['param'].get('orde'))))
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

    if not args.tanpa_rmf2:
        baris('.rmf versi 2', lambda: rf2.encode(data)[0])
    baris('.rmf versi 3', lambda: encode(data)[0])
    baris('zlib -9 (zip)', lambda: zlib.compress(data, 9))
    baris('lzma -9e (7z)', lambda: lzma.compress(data, preset=9 | lzma.PRESET_EXTREME))


def main():
    parser = argparse.ArgumentParser(
        description='Return[er] Machine Final v3: mode campuran per blok + konteks versi 2 + SHA-256 (.rmf).')
    sub = parser.add_subparsers(dest='perintah', required=True)

    p = sub.add_parser('encode', help='file asli -> file .rmf versi 3')
    p.add_argument('input')
    p.add_argument('-o', '--output', help='nama file .rmf (default: <input>.rmf)')
    p.add_argument('-b', '--blok', type=int, default=BLOK_DEFAULT,
                   help='ukuran blok dalam byte (default: %d)' % BLOK_DEFAULT)
    p.add_argument('-a', '--ambang', type=float, default=AMBANG_DEFAULT,
                   help='blok dengan entropy di atas ambang disimpan mentah (default: %.1f bit/byte, 8 = semua dikodekan)' % AMBANG_DEFAULT)
    p.add_argument('-k', '--orde', type=int, choices=range(0, rk2.ORDE_MAKS + 1), metavar='0..%d' % rk2.ORDE_MAKS,
                   help='paksa mode konteks2 dengan orde ini untuk bagian berpola')
    p.add_argument('--tanpa-verifikasi', action='store_true', help='jangan decode ulang setelah encode')
    p.set_defaults(func=cmd_encode)

    p = sub.add_parser('decode', help='file .rmf (versi 1, 2, atau 3) -> file asli')
    p.add_argument('input')
    p.add_argument('-o', '--output', help='nama file hasil (default: <input tanpa .rmf>.decoded)')
    p.set_defaults(func=cmd_decode)

    p = sub.add_parser('info', help='tampilkan header dan peta blok tanpa decode')
    p.add_argument('input')
    p.add_argument('--semua', action='store_true', help='tampilkan seluruh peta blok')
    p.set_defaults(func=cmd_info)

    p = sub.add_parser('bandingkan', help='bandingkan .rmf versi 2, versi 3, zip, dan 7z (tanpa menulis file)')
    p.add_argument('input')
    p.add_argument('--tanpa-rmf2', action='store_true', help='lewati .rmf versi 2 (lebih cepat)')
    p.set_defaults(func=cmd_bandingkan)

    args = parser.parse_args()
    if args.perintah == 'encode' and not 0 <= args.ambang <= 8:
        sys.exit('Ambang harus di antara 0 dan 8')
    args.func(args)


if __name__ == '__main__':
    main()
