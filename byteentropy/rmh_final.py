import sys
import time
import hashlib
import argparse

import rmh
import rmh_adaptif as ra
import rmh_konteks as rk
# rmh_final.py - Return[er] Machine Final
# Menggabungkan metode terbaik dari tahap sebelumnya:
#   - memilih mode secara otomatis: konteks (.rmk, orde 1..5), adaptif (.rma),
#     atau mentah jika data tidak bisa diperkecil (acak / sudah terkompresi);
#   - SHA-256 file asli di header sebagai sidik jari berukuran tetap (32 byte),
#     sekaligus memastikan file yang digenerate kembali benar-benar identik.
# Hasilnya deterministik: file yang sama selalu menghasilkan .rmf yang sama.
#
# Format file .rmf (varint = LEB128):
#   [4 byte ] magic "RMF1"
#   [1 byte ] mode       : 0 = mentah, 1 = adaptif, 2 = konteks
#   [varint ] n          : ukuran file asli (byte)
#   [32 byte] SHA-256 file asli
#   parameter mode:
#     mode 1: [varint] tambah, [varint] batas
#     mode 2: [1 byte] orde
#   [sisa   ] data mentah (mode 0) atau bit arithmetic coding (mode 1, 2)

MAGIC = b'RMF1'
MENTAH, ADAPTIF, KONTEKS = 0, 1, 2
NAMA_MODE = {MENTAH: 'mentah', ADAPTIF: 'adaptif', KONTEKS: 'konteks'}
ORDE_KANDIDAT = (1, 2, 3, 4, 5)
BATAS_UJI_PENUH = 256 * 1024    # file lebih besar: pilih mode dari sampel
UKURAN_SAMPEL = 64 * 1024       # diambil dari awal, tengah, dan akhir file


# ---------- pemilihan mode ----------

def nama_kandidat(mode, orde=None):
    return 'konteks orde %d' % orde if mode == KONTEKS else NAMA_MODE[mode]


def kodekan(data, mode, orde=None):
    if mode == KONTEKS:
        return rk.kodekan_konteks(data, orde)[0]
    if mode == ADAPTIF:
        return ra.kode_aritmetika(data, ra.TAMBAH_DEFAULT, ra.BATAS_DEFAULT)
    return bytes(data)


def ambil_sampel(data):
    if len(data) <= 3 * UKURAN_SAMPEL:
        return data
    tengah = (len(data) - UKURAN_SAMPEL) // 2
    return data[:UKURAN_SAMPEL] + data[tengah:tengah + UKURAN_SAMPEL] + data[-UKURAN_SAMPEL:]


def pilih_mode(data, orde_paksa=None):
    # Mengembalikan (mode, orde, kode atau None, daftar hasil uji, pakai_sampel)
    # Kandidat diuji berurutan; jika ukurannya sama, yang lebih awal (lebih sederhana) dipilih.
    if orde_paksa is not None:
        kandidat = [(KONTEKS, orde_paksa)]
    else:
        kandidat = [(MENTAH, None), (ADAPTIF, None)] + [(KONTEKS, k) for k in ORDE_KANDIDAT]
    pakai_sampel = len(data) > BATAS_UJI_PENUH and orde_paksa is None
    uji = ambil_sampel(data) if pakai_sampel else data

    hasil = []
    terbaik = None
    for mode, orde in kandidat:
        mulai = time.perf_counter()
        kode = kodekan(uji, mode, orde)
        hasil.append((nama_kandidat(mode, orde), len(uji), len(kode), time.perf_counter() - mulai))
        if terbaik is None or len(kode) < len(terbaik[2]):
            terbaik = (mode, orde, kode)

    mode, orde, kode = terbaik
    if pakai_sampel:
        kode = None     # kode sampel tidak dipakai, file penuh dikodekan ulang
    return mode, orde, kode, hasil, pakai_sampel


# ---------- format file .rmf ----------

def susun_header(mode, n, sha, orde):
    header = MAGIC + bytes([mode]) + rmh.tulis_varint(n) + sha
    if mode == ADAPTIF:
        header += rmh.tulis_varint(ra.TAMBAH_DEFAULT) + rmh.tulis_varint(ra.BATAS_DEFAULT)
    elif mode == KONTEKS:
        header += bytes([orde])
    return header


def encode(data, orde_paksa=None):
    sha = hashlib.sha256(data).digest()
    if not data:
        return susun_header(MENTAH, 0, sha, None), {'mode': MENTAH, 'orde': None, 'uji': [], 'sampel': False, 'penuh': []}

    mode, orde, kode, uji, pakai_sampel = pilih_mode(data, orde_paksa)
    penuh = []
    if kode is None:
        mulai = time.perf_counter()
        kode = kodekan(data, mode, orde)
        penuh.append((nama_kandidat(mode, orde), len(kode), time.perf_counter() - mulai))
        # Sampel cenderung memilih orde terlalu rendah, karena konteks panjang belum
        # sempat dipelajari. Pada file penuh, coba orde berikutnya selama hasilnya mengecil.
        while mode == KONTEKS and orde < max(ORDE_KANDIDAT):
            mulai = time.perf_counter()
            kode_lain = kodekan(data, KONTEKS, orde + 1)
            penuh.append((nama_kandidat(KONTEKS, orde + 1), len(kode_lain), time.perf_counter() - mulai))
            if len(kode_lain) >= len(kode):
                break
            kode, orde = kode_lain, orde + 1
    if mode != MENTAH and len(kode) >= len(data):
        # hasil pada file penuh ternyata tidak lebih kecil: simpan mentah
        mode, orde, kode = MENTAH, None, bytes(data)
    info = {'mode': mode, 'orde': orde, 'uji': uji, 'sampel': pakai_sampel, 'penuh': penuh}
    return susun_header(mode, len(data), sha, orde) + kode, info


def baca_rmf(isi):
    if isi[:4] != MAGIC:
        raise ValueError('Bukan file .rmf (magic tidak cocok)')
    if len(isi) < 5:
        raise ValueError('File .rmf terpotong (header tidak lengkap)')
    mode = isi[4]
    if mode not in NAMA_MODE:
        raise ValueError('Mode tidak dikenal: %d' % mode)
    try:
        n, pos = rmh.baca_varint(isi, 5)
        if pos + 32 > len(isi):
            raise ValueError
        sha = isi[pos:pos + 32]
        pos += 32
        param = {}
        if mode == ADAPTIF:
            param['tambah'], pos = rmh.baca_varint(isi, pos)
            param['batas'], pos = rmh.baca_varint(isi, pos)
        elif mode == KONTEKS:
            if pos >= len(isi):
                raise ValueError
            param['orde'] = isi[pos]
            pos += 1
    except ValueError:
        raise ValueError('File .rmf terpotong (header tidak lengkap)')
    if mode == KONTEKS and param['orde'] > rk.ORDE_MAKS:
        raise ValueError('Orde tidak valid: %d' % param['orde'])
    if mode == ADAPTIF and not (1 <= param['tambah'] <= 1 << 16 and 512 <= param['batas'] <= 1 << 24):
        raise ValueError('Parameter adaptif tidak valid')
    if mode == MENTAH and len(isi) - pos != n:
        raise ValueError('Panjang data mentah tidak sesuai (diharapkan %d byte, ada %d)' % (n, len(isi) - pos))
    return mode, n, sha, param, pos


def decode(isi):
    mode, n, sha, param, pos = baca_rmf(isi)
    kode = isi[pos:]
    if mode == MENTAH:
        data = bytes(kode)
    elif mode == ADAPTIF:
        data = ra.dekode_aritmetika(kode, n, param['tambah'], param['batas']) if n else b''
    else:
        data = rk.dekode_konteks(kode, n, param['orde']) if n else b''
    if hashlib.sha256(data).digest() != sha:
        raise ValueError('SHA-256 tidak cocok, hasil decode rusak')
    return data


# ---------- perintah ----------

def cmd_encode(args):
    data = rmh.baca_file(args.input)
    output = args.output or args.input + '.rmf'
    mulai = time.perf_counter()
    try:
        isi, info = encode(data, args.orde)
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
    if info['uji']:
        print('Uji kandidat (%s):' % ('sampel %d byte dari awal, tengah, akhir file' % info['uji'][0][1]
                                       if info['sampel'] else 'file penuh'))
        print('  %-18s %12s %9s %9s' % ('Kandidat', 'Kode (byte)', '% uji', 'Detik'))
        terpilih = nama_kandidat(info['mode'], info['orde'])
        terbaik_uji = min(info['uji'], key=lambda u: u[2])[0]
        for nama, ukuran_uji, ukuran, detik in info['uji']:
            tanda = '  <- terpilih' if nama == terpilih and not info['penuh'] else (
                '  <- terbaik di sampel' if nama == terbaik_uji and info['penuh'] else '')
            print('  %-18s %12d %8.1f%% %9.3f%s' % (nama, ukuran, ukuran / ukuran_uji * 100, detik, tanda))
        print()
    if info['penuh']:
        print('Penyesuaian pada file penuh (orde dinaikkan selama hasil mengecil):')
        print('  %-18s %12s %9s %9s' % ('Kandidat', 'Kode (byte)', '% asli', 'Detik'))
        for nama, ukuran, detik in info['penuh']:
            tanda = '  <- terpilih' if nama == nama_kandidat(info['mode'], info['orde']) else ''
            print('  %-18s %12d %8.1f%% %9.3f%s' % (nama, ukuran, ukuran / len(data) * 100, detik, tanda))
        print()
    print('Encode     :', args.input, '->', output, '(%.3f detik)' % durasi)
    print('Mode       :', nama_kandidat(info['mode'], info['orde']))
    print('SHA-256    :', hashlib.sha256(data).hexdigest())
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
    try:
        mode, n, sha, param, pos = baca_rmf(isi)
    except ValueError as e:
        sys.exit('File tidak valid: %s' % e)
    print('File .rmf        :', args.input, '(%d byte)' % len(isi))
    print('Mode             :', nama_kandidat(mode, param.get('orde')))
    if mode == ADAPTIF:
        print('Parameter        : tambah=%d, batas=%d' % (param['tambah'], param['batas']))
    print('Ukuran file asli :', n, 'byte')
    print('SHA-256 asli     :', sha.hex())
    print('Header           :', pos, 'byte')
    print('Kode / data      :', len(isi) - pos, 'byte')
    print('Rasio            :', rmh.persen(len(isi), n))


def main():
    parser = argparse.ArgumentParser(description='Return[er] Machine Final: mode otomatis + SHA-256 (.rmf).')
    sub = parser.add_subparsers(dest='perintah', required=True)

    p = sub.add_parser('encode', help='file asli -> file .rmf (mode dipilih otomatis)')
    p.add_argument('input')
    p.add_argument('-o', '--output', help='nama file .rmf (default: <input>.rmf)')
    p.add_argument('-k', '--orde', type=int, choices=range(0, rk.ORDE_MAKS + 1), metavar='0..%d' % rk.ORDE_MAKS,
                   help='paksa mode konteks dengan orde ini (default: pilih otomatis)')
    p.add_argument('--tanpa-verifikasi', action='store_true',
                   help='jangan decode ulang untuk memastikan hasilnya identik (lebih cepat)')
    p.set_defaults(func=cmd_encode)

    p = sub.add_parser('decode', help='file .rmf -> file asli, diverifikasi SHA-256')
    p.add_argument('input')
    p.add_argument('-o', '--output', help='nama file hasil (default: <input tanpa .rmf>.decoded)')
    p.set_defaults(func=cmd_decode)

    p = sub.add_parser('info', help='tampilkan header file .rmf (mode, ukuran, SHA-256) tanpa decode')
    p.add_argument('input')
    p.set_defaults(func=cmd_info)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
