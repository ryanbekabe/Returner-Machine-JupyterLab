import sys
import math
import time
import zlib
import argparse
from collections import Counter

import rmh
import rmh_konteks as rk
# rmh_konteks_info.py - melihat bagaimana file .rmk menyimpan data
# File .rmk hanya berisi header + CRC32 + bit arithmetic coding. Histogram per
# konteks TIDAK disimpan, jadi untuk melihat isinya file didekode ulang sambil
# mencatat: konteks mana yang dipakai, berapa kali ESCAPE, dan berapa bit yang
# dihabiskan setiap byte. Biaya satu kejadian = log2(total / lebar interval).


def tampil_byte(b):
    if b == 0x5C:
        return '\\\\'
    if 32 <= b < 127:
        return chr(b)
    return {9: '\\t', 10: '\\n', 13: '\\r'}.get(b, '\\x%02X' % b)


def tampil(bs):
    return ''.join(tampil_byte(b) for b in bs)


def kutip_byte(b):
    return "'%s'" % tampil_byte(b).replace("'", "\\'")


def kutip_teks(bs):
    return '"%s"' % tampil(bs).replace('"', '\\"')


def heksa(bs):
    return ' '.join('%02X' % b for b in bs)


def segmen_baru():
    return {'panjang': 0, 'bit': 0.0, 'orde_maks': 0, 'escape': 0, 'baru': 0}


def putar_ulang(isi, ukuran_segmen, jejak_dari, jejak_jumlah):
    # Sama seperti rk.dekode_konteks(), ditambah pencatatan di setiap langkah
    n, orde, crc, kode = rk.baca_rmk(isi)
    model = rk.ModelPPM(orde)
    dec = rk.Decoder(kode)
    hasil = bytearray()

    per_orde = {k: [0, 0.0] for k in range(-1, orde + 1)}   # orde -> [jumlah byte, bit]
    escape = [0, 0.0]
    dipakai = Counter()     # (orde, konteks) -> berapa byte berhasil ditebak di konteks itu
    segmen = []
    seg = segmen_baru()
    jejak = []

    for posisi in range(n):
        dikecualikan = set()
        x = None
        langkah = []
        bit_byte = 0.0
        for k, konteks in model.daftar_konteks():
            if not konteks:
                langkah.append('o%d:-' % k)
                continue
            daftar, cum_byte, total = rk._interval(konteks, dikecualikan)
            if not daftar:
                langkah.append('o%d:-' % k)
                continue
            t = dec.target(total)
            if t < cum_byte:
                for s, lo, hi in daftar:
                    if lo <= t < hi:
                        dec.konsumsi(lo, hi, total)
                        x = s
                        bit = math.log2(total / (hi - lo))
                        break
                per_orde[k][0] += 1
                per_orde[k][1] += bit
                bit_byte += bit
                langkah.append('o%d:OK %.2f' % (k, bit))
                dipakai[(k, model.riwayat & ((1 << (8 * k)) - 1))] += 1
                if k == orde:
                    seg['orde_maks'] += 1
                break
            dec.konsumsi(cum_byte, total, total)    # ESCAPE
            bit = math.log2(total / (total - cum_byte))
            escape[0] += 1
            escape[1] += bit
            bit_byte += bit
            seg['escape'] += 1
            langkah.append('o%d:ESC %.2f' % (k, bit))
            dikecualikan.update(s for s, _, _ in daftar)
        if x is None:
            sisa = [s for s in range(256) if s not in dikecualikan]
            i = dec.target(len(sisa))
            if i >= len(sisa):
                raise ValueError('Kode rusak (indeks byte di luar jangkauan)')
            dec.konsumsi(i, i + 1, len(sisa))
            x = sisa[i]
            bit = math.log2(len(sisa))
            per_orde[-1][0] += 1
            per_orde[-1][1] += bit
            bit_byte += bit
            seg['baru'] += 1
            langkah.append('o-1:BARU %.2f' % bit)

        if jejak_dari <= posisi < jejak_dari + jejak_jumlah:
            jejak.append((posisi, x, bytes(hasil[max(0, posisi - orde):posisi]), langkah, bit_byte))
        hasil.append(x)
        model.perbarui(x)

        seg['panjang'] += 1
        seg['bit'] += bit_byte
        if seg['panjang'] == ukuran_segmen or posisi == n - 1:
            segmen.append(seg)
            seg = segmen_baru()

    if zlib.crc32(hasil) != crc:
        raise ValueError('CRC32 tidak cocok, hasil decode rusak')
    return {'n': n, 'orde': orde, 'crc': crc, 'kode': kode, 'model': model, 'per_orde': per_orde,
            'escape': escape, 'dipakai': dipakai, 'segmen': segmen, 'jejak': jejak}


def cetak_header(args, isi, h):
    kode = h['kode']
    panjang_header = len(isi) - len(kode) - 4
    panjang_n = panjang_header - 5
    print('File .rmk        :', args.input, '(%d byte)' % len(isi))
    print('Ukuran file asli :', h['n'], 'byte')
    print('Orde maksimum    :', h['orde'])
    print('CRC32            : %08X' % h['crc'])
    print()
    print('Isi file (yang benar-benar tersimpan):')
    print('  %6s %7s  %-7s %s' % ('Offset', 'Ukuran', 'Bagian', 'Isi'))
    print('  %6d %7d  %-7s %-24s ("RMK1")' % (0, 4, 'magic', heksa(isi[:4])))
    print('  %6d %7d  %-7s %-24s (%d)' % (4, panjang_n, 'n', heksa(isi[4:4 + panjang_n]), h['n']))
    print('  %6d %7d  %-7s %-24s (%d)' % (4 + panjang_n, 1, 'orde', heksa(isi[4 + panjang_n:5 + panjang_n]), h['orde']))
    print('  %6d %7d  %-7s %s' % (panjang_header, 4, 'crc32', heksa(isi[panjang_header:panjang_header + 4])))
    contoh = heksa(kode[:6]) + (' ...' if len(kode) > 6 else '')
    print('  %6d %7d  %-7s %-24s (bit arithmetic coding)' % (panjang_header + 4, len(kode), 'kode', contoh))
    print('  Histogram / konteks : 0 byte (tidak disimpan, dibangun ulang saat decode)')


def cetak_segmen(args, isi, h):
    segmen = h['segmen']
    offset_kode = len(isi) - len(h['kode'])
    print('Rincian per segmen %d byte (didapat dengan memutar ulang decode):' % args.segmen)
    print('  %6s %8s %8s %12s %9s %8s %8s %6s' % ('Segmen', 'Panjang', 'Offset', 'Kode (byte)', 'bit/byte',
                                                'Orde %d' % h['orde'], 'Escape', 'Baru'))
    awal_bit = [0.0]
    for s in segmen:
        awal_bit.append(awal_bit[-1] + s['bit'])
    if args.semua or len(segmen) <= 20:
        nomor_tampil = list(range(len(segmen)))
    else:
        nomor_tampil = list(range(10)) + [None] + list(range(len(segmen) - 5, len(segmen)))
    for nomor in nomor_tampil:
        if nomor is None:
            print('  %6s' % '...')
            continue
        s = segmen[nomor]
        print('  %6d %8d %8d %12.1f %9.3f %7.1f%% %8d %6d' % (
            nomor, s['panjang'], offset_kode + int(awal_bit[nomor] // 8), s['bit'] / 8, s['bit'] / s['panjang'],
            s['orde_maks'] / s['panjang'] * 100, s['escape'], s['baru']))


def cetak_ringkasan(h):
    n = h['n']
    total_bit = sum(b for _, b in h['per_orde'].values()) + h['escape'][1]
    print('Ke mana bit kode dihabiskan:')
    print('  %-22s %9s %12s %14s' % ('Kejadian', 'Jumlah', 'Kode (byte)', 'Rata-rata bit'))
    for k in range(h['orde'], -1, -1):
        jumlah, bit = h['per_orde'][k]
        print('  %-22s %9d %12.1f %14.3f' % ('byte di orde %d' % k, jumlah, bit / 8, bit / jumlah if jumlah else 0))
    jumlah, bit = h['per_orde'][-1]
    print('  %-22s %9d %12.1f %14.3f' % ('byte baru (orde -1)', jumlah, bit / 8, bit / jumlah if jumlah else 0))
    jumlah, bit = h['escape']
    print('  %-22s %9d %12.1f %14.3f' % ('ESCAPE', jumlah, bit / 8, bit / jumlah if jumlah else 0))
    print('  %-22s %9d %12.1f %14.3f' % ('TOTAL (per byte asli)', n, total_bit / 8, total_bit / n))
    print('  Kode sebenarnya: %d byte (selisih = presisi arithmetic coder + bantalan akhir)' % len(h['kode']))


def cetak_konteks(args, h):
    model = h['model']
    orde = h['orde']
    print('Konteks yang dipelajari (tidak disimpan di file, dibangun ulang saat decode):')
    for k in range(orde, -1, -1):
        print('  orde %d : %6d konteks' % (k, len(model.tabel[k])))
    if args.konteks <= 0:
        return
    teratas = [(kunci, jumlah) for (k, kunci), jumlah in h['dipakai'].most_common() if k == orde][:args.konteks]
    if not teratas:
        return
    print()
    teks = [kutip_teks(kunci.to_bytes(orde, 'big') if orde else b'') for kunci, _ in teratas]
    lebar = max(len('Konteks'), *(len(t) for t in teks))
    print('%d konteks orde %d yang paling sering menebak dengan benar:' % (len(teratas), orde))
    print('  %-*s %8s  %s' % (lebar, 'Konteks', 'Benar', 'Byte berikutnya (frekuensi saat ini)'))
    for (kunci, jumlah), konteks in zip(teratas, teks):
        frek = sorted(model.tabel[orde][kunci].items(), key=lambda p: -p[1])
        isi = ' '.join('%s:%d' % (kutip_byte(s), f) for s, f in frek[:6])
        if len(frek) > 6:
            isi += ' ... (+%d)' % (len(frek) - 6)
        print('  %-*s %8d  %s' % (lebar, konteks, jumlah, isi))


def cetak_jejak(args, h):
    if not h['jejak']:
        print('Jejak: posisi %d di luar ukuran file.' % args.dari)
        return
    awal, akhir = h['jejak'][0][0], h['jejak'][-1][0]
    print('Jejak decode byte %d..%d (o<k> = konteks orde k, - = konteks belum ada, angka = bit):' % (awal, akhir))
    lebar = max(len('Konteks'), *(len(kutip_teks(j[2])) for j in h['jejak']))
    print('  %7s %-6s %-*s %7s  %s' % ('Posisi', 'Byte', lebar, 'Konteks', 'Bit', 'Langkah'))
    for posisi, x, konteks, langkah, bit in h['jejak']:
        print('  %7d %-6s %-*s %7.2f  %s' % (posisi, kutip_byte(x), lebar, kutip_teks(konteks), bit,
                                            '  '.join(langkah)))


def main():
    parser = argparse.ArgumentParser(description='Lihat bagaimana file .rmk (rmh_konteks.py) menyimpan data.')
    parser.add_argument('input', help='file .rmk')
    parser.add_argument('-s', '--segmen', type=int, default=4096,
                        help='ukuran segmen untuk tabel rincian (default: 4096, sama dengan blok .rmb)')
    parser.add_argument('--semua', action='store_true', help='tampilkan semua segmen')
    parser.add_argument('-t', '--konteks', type=int, default=10,
                        help='jumlah konteks teratas yang ditampilkan (default: 10, 0 = tidak)')
    parser.add_argument('--jejak', type=int, default=0, metavar='N',
                        help='tampilkan langkah decode untuk N byte (default: 0 = tidak)')
    parser.add_argument('--dari', type=int, default=0, metavar='POSISI',
                        help='posisi awal jejak (default: 0)')
    args = parser.parse_args()
    if args.segmen < 1 or args.jejak < 0 or args.dari < 0:
        sys.exit('Nilai --segmen minimal 1, --jejak dan --dari tidak boleh negatif')

    isi = rmh.baca_file(args.input)
    mulai = time.perf_counter()
    try:
        h = putar_ulang(isi, args.segmen, args.dari, args.jejak)
    except ValueError as e:
        sys.exit('File tidak valid: %s' % e)
    durasi = time.perf_counter() - mulai

    cetak_header(args, isi, h)
    if h['n'] == 0:
        print()
        print('File asli kosong, tidak ada data untuk ditampilkan.')
        return
    print()
    cetak_segmen(args, isi, h)
    print()
    cetak_ringkasan(h)
    print()
    cetak_konteks(args, h)
    if args.jejak:
        print()
        cetak_jejak(args, h)
    print()
    print('(memutar ulang decode: %.3f detik, CRC32 cocok)' % durasi)


if __name__ == '__main__':
    main()
