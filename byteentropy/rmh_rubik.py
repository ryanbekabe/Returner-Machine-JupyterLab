import sys
import math
import html
import argparse

import rmh
import rmh_final2 as rf2
# rmh_rubik.py - Return[er] Machine Rubik's DNA
# Merepresentasikan file sebagai deretan kubus Rubik 4x4x4.
# Setiap kubus punya jumlah warna TETAP: 6 warna x 16 stiker = 96 stiker
# (histogram tetap), tetapi susunan warnanya bisa beragam (permutasi).
# Susunan warna = rank permutasi, dihitung dengan rmh.rank() / rmh.unrank(),
# yaitu enumerative coding yang sama dengan rmh.py.
#
#   jumlah susunan per kubus = 96! / (16!^6) = 1,18 x 10^70 = 232,8 bit
#   -> setiap kubus menyimpan 29 byte
#
# Alur:  file -> .rmf (rmh_final2, dikompresi + SHA-256)
#             -> [varint panjang] + isi .rmf
#             -> dipotong per 29 byte -> setiap potongan = satu susunan kubus
# Kubus yang sudah tersusun (setiap sisi satu warna) adalah rank 0.
#
# Catatan: tidak semua susunan stiker bisa dicapai dengan memutar kubus fisik
# (yang bisa dicapai "hanya" 7,4 x 10^45 = 152,4 bit). Di sini kubus dipakai
# sebagai wadah stiker berwarna dengan jumlah warna tetap.

SISI = 'ULFRBD'                         # atas, kiri, depan, kanan, belakang, bawah
WARNA = 'WOGRBY'                        # putih, oranye, hijau, merah, biru, kuning
NAMA_WARNA = ['putih', 'oranye', 'hijau', 'merah', 'biru', 'kuning']
HEX_WARNA = ['#f4f4f4', '#f28a1e', '#1aa34a', '#d62f2f', '#2a62d6', '#f5d60f']
STIKER = 16
HISTOGRAM = {w: STIKER for w in range(6)}
SUSUNAN = math.factorial(96) // math.factorial(STIKER) ** 6
BYTE_PER_KUBUS = int(math.log2(SUSUNAN)) // 8      # 29


# ---------- data <-> kubus ----------

def ke_kubus(muatan):
    # muatan (bytes) -> daftar kubus, setiap kubus = 96 angka warna 0..5
    data = rmh.tulis_varint(len(muatan)) + muatan
    data += bytes(-len(data) % BYTE_PER_KUBUS)
    kubus = []
    for i in range(0, len(data), BYTE_PER_KUBUS):
        r = int.from_bytes(data[i:i + BYTE_PER_KUBUS], 'big')
        kubus.append(list(rmh.unrank(r, HISTOGRAM)))
    return kubus


def dari_kubus(kubus):
    data = bytearray()
    for nomor, stiker in enumerate(kubus):
        if len(stiker) != 96 or any(stiker.count(w) != STIKER for w in range(6)):
            raise ValueError('Kubus %d tidak valid: harus 96 stiker, 16 untuk setiap warna' % nomor)
        r = rmh.rank(bytes(stiker), HISTOGRAM)
        if r >= 1 << (8 * BYTE_PER_KUBUS):
            raise ValueError('Kubus %d berisi susunan di luar jangkauan 29 byte' % nomor)
        data += r.to_bytes(BYTE_PER_KUBUS, 'big')
    panjang, pos = rmh.baca_varint(bytes(data), 0)
    if pos + panjang > len(data):
        raise ValueError('Jumlah kubus kurang dari yang dibutuhkan')
    return bytes(data[pos:pos + panjang])


# ---------- tampilan ----------

def baris_teks(stiker):
    # 96 stiker -> satu baris huruf, dikelompokkan per sisi
    return ' '.join(''.join(WARNA[w] for w in stiker[s * 16:(s + 1) * 16]) for s in range(6))


def baca_baris(baris):
    huruf = baris.replace(' ', '')
    if any(h not in WARNA for h in huruf):
        raise ValueError('Huruf warna tidak dikenal: %s' % ''.join(sorted(set(huruf) - set(WARNA))))
    return [WARNA.index(h) for h in huruf]


def jaring(stiker):
    # jaring kubus seperti gambar Returner Machine Rubik DNA: U di atas, L F R B di tengah, D di bawah
    sisi = [stiker[s * 16:(s + 1) * 16] for s in range(6)]
    baris = lambda s, r: ' '.join(WARNA[w] for w in sisi[s][r * 4:r * 4 + 4])
    kosong = ' ' * 8
    hasil = []
    for r in range(4):
        hasil.append(kosong + '  ' + baris(0, r))
    for r in range(4):
        hasil.append('  '.join(baris(s, r) for s in (1, 2, 3, 4)))
    for r in range(4):
        hasil.append(kosong + '  ' + baris(5, r))
    return hasil


def tulis_html(nama_file, kubus, judul, maks):
    def svg(stiker):
        posisi = {0: (1, 0), 1: (0, 1), 2: (1, 1), 3: (2, 1), 4: (3, 1), 5: (1, 2)}
        s, isi = 13, []
        for f in range(6):
            fx, fy = posisi[f]
            for i, w in enumerate(stiker[f * 16:(f + 1) * 16]):
                x = (fx * 4 + i % 4) * s + fx * 3
                y = (fy * 4 + i // 4) * s + fy * 3
                isi.append('<rect x="%d" y="%d" width="%d" height="%d" rx="2" fill="%s" stroke="#222" stroke-width="1"/>'
                           % (x, y, s - 1, s - 1, HEX_WARNA[w]))
        return '<svg viewBox="-2 -2 %d %d" width="%d" height="%d">%s</svg>' % (16 * s + 13, 12 * s + 10, 16 * s + 13, 12 * s + 10, ''.join(isi))

    kartu = ''.join('<figure><figcaption>kubus %d</figcaption>%s</figure>' % (i, svg(k)) for i, k in enumerate(kubus[:maks]))
    lebih = '' if len(kubus) <= maks else '<p>... dan %d kubus lainnya (lihat file teks).</p>' % (len(kubus) - maks)
    halaman = ('<!doctype html><meta charset="utf-8"><title>%s</title>'
               '<style>body{font-family:system-ui,sans-serif;background:#f6f7f9;color:#111;margin:24px}'
               '.grid{display:flex;flex-wrap:wrap;gap:14px}figure{margin:0;background:#fff;border:1px solid #dde;'
               'border-radius:8px;padding:8px}figcaption{font:12px monospace;color:#556;margin-bottom:4px}</style>'
               '<h1>%s</h1><p>%d kubus 4x4x4, setiap kubus 6 warna x 16 stiker, menyimpan %d byte.</p>'
               '<div class="grid">%s</div>%s') % (html.escape(judul), html.escape(judul), len(kubus), BYTE_PER_KUBUS, kartu, lebih)
    rmh.tulis_file(nama_file, halaman.encode('utf-8'))


# ---------- perintah ----------

def cmd_encode(args):
    data = rmh.baca_file(args.input)
    try:
        muatan, info = rf2.encode(data)
    except ValueError as e:
        sys.exit('Encode gagal: %s' % e)
    kubus = ke_kubus(muatan)
    if dari_kubus(kubus) != muatan or rf2.decode(muatan) != data:
        sys.exit('Verifikasi GAGAL. File tidak ditulis.')

    output = args.output or args.input + '.kubus.txt'
    teks = ['# Return[er] Machine Rubik\'s DNA',
            '# Setiap baris "kubus" = 96 stiker dalam urutan sisi %s, 16 stiker per sisi.' % ' '.join(SISI),
            '# Warna: ' + ', '.join('%s=%s' % (WARNA[w], NAMA_WARNA[w]) for w in range(6)) + '. Setiap kubus: 16 stiker per warna.',
            '# File asli: %s (%d byte), .rmf %d byte, %d kubus x %d byte' % (args.input, len(data), len(muatan), len(kubus), BYTE_PER_KUBUS)]
    teks += ['kubus %d: %s' % (i, baris_teks(k)) for i, k in enumerate(kubus)]
    rmh.tulis_file(output, ('\n'.join(teks) + '\n').encode('utf-8'))

    print('File asli        : %s (%d byte)' % (args.input, len(data)))
    print('Setelah .rmf     : %d byte (%s)' % (len(muatan), rf2.rf.nama_kandidat(info['mode'], info['orde'])))
    print('Kapasitas kubus  : 96!/(16!^6) = %.3e susunan = %.1f bit -> %d byte per kubus' % (
        SUSUNAN, math.log2(SUSUNAN), BYTE_PER_KUBUS))
    print('Jumlah kubus     : %d' % len(kubus))
    print('Ditulis ke       : %s' % output)
    if args.html:
        tulis_html(args.html, kubus, 'Rubik DNA: %s' % args.input, args.maks)
        print('Gambar kubus     : %s (%d kubus pertama)' % (args.html, min(args.maks, len(kubus))))
    for i in range(min(args.tampil, len(kubus))):
        print()
        print('kubus %d:' % i)
        for b in jaring(kubus[i]):
            print('  ' + b)


def cmd_decode(args):
    kubus = []
    try:
        for baris in rmh.baca_file(args.input).decode('utf-8').splitlines():
            if baris.startswith('kubus '):
                kubus.append(baca_baris(baris.split(':', 1)[1]))
        data = rf2.decode(dari_kubus(kubus))
    except (ValueError, UnicodeDecodeError) as e:
        sys.exit('Decode gagal: %s' % e)
    output = args.output or (args.input[:-len('.kubus.txt')] if args.input.endswith('.kubus.txt') else args.input) + '.decoded'
    rmh.tulis_file(output, data)
    print('Decode  : %d kubus -> %s (%d byte, SHA-256 cocok)' % (len(kubus), output, len(data)))


def main():
    parser = argparse.ArgumentParser(description="Return[er] Machine Rubik's DNA: file <-> deretan kubus Rubik 4x4x4.")
    sub = parser.add_subparsers(dest='perintah', required=True)

    p = sub.add_parser('encode', help='file -> kubus (file teks, opsional gambar HTML)')
    p.add_argument('input')
    p.add_argument('-o', '--output', help='file teks kubus (default: <input>.kubus.txt)')
    p.add_argument('--html', help='simpan gambar kubus ke file HTML')
    p.add_argument('--maks', type=int, default=300, help='jumlah kubus maksimum di HTML (default: 300)')
    p.add_argument('--tampil', type=int, default=1, help='jumlah jaring kubus yang dicetak (default: 1)')
    p.set_defaults(func=cmd_encode)

    p = sub.add_parser('decode', help='file teks kubus -> file asli')
    p.add_argument('input')
    p.add_argument('-o', '--output', help='nama file hasil')
    p.set_defaults(func=cmd_decode)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
