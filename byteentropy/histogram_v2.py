import sys
import math
import argparse
from collections import Counter
# histogram_v2.py - perbaikan histogram.py
# - Index = nilai byte 0..255 (bukan urutan kemunculan Counter)
# - Semua 256 nilai byte ditampilkan, termasuk yang frekuensinya 0
# - Nama file yang mengandung spasi ditangani oleh argparse

parser = argparse.ArgumentParser(description='Byte histogram dan Shannon entropy sebuah file.')
parser.add_argument('namafile', help='file yang akan dianalisis')
parser.add_argument('--semua', action='store_true', help='tampilkan juga byte yang frekuensinya 0')
parser.add_argument('--plot', metavar='PNG', help='simpan grafik histogram ke file PNG')
args = parser.parse_args()

try:
    with open(args.namafile, 'rb') as fd:
        contents = fd.read()
except OSError as e:
    sys.exit('Gagal membuka file: %s' % e)

l = len(contents)
print('Ukuran file dalam bytes:', l)
if l == 0:
    sys.exit('File kosong, histogram dan entropy tidak dapat dihitung.')

c = Counter(contents)

# Histogram: frekuensi setiap nilai byte 0..255
histogram = [c.get(b, 0) for b in range(256)]

print()
print('Histogramnya adalah:')
print('%5s %4s %5s %12s %9s %12s' % ('Byte', 'Hex', 'Char', 'Frekuensi', 'Persen', '-p*log2(p)'))
e = 0.0
for byte_value, count in enumerate(histogram):
    if count == 0 and not args.semua:
        continue
    p_x = count / l
    d = -p_x * math.log2(p_x) if count > 0 else 0.0
    e += d
    char = chr(byte_value) if 32 <= byte_value < 127 else '.'
    print('%5d %4s %5s %12d %8.4f%% %12.6f' % (byte_value, '%02X' % byte_value, char, count, p_x * 100, d))

print('----')
print('Jumlah nilai byte berbeda yang muncul =', len(c), 'dari 256')
print('Total byte (sum frekuensi)            =', sum(histogram))
print('Frekuensi min (yang muncul)           =', min(c.values()))
print('Frekuensi max                         =', max(c.values()))
print()
print('Shannon entropy (bits per byte, 0..8) =', e)
print('Min kemungkinan ukuran file dengan asumsi efisiensi kompresi teoretis maks:')
print(e * l, 'in bits')
print(e * l / 8, 'in bytes')

if args.plot:
    try:
        import matplotlib
    except ImportError:
        sys.exit('Opsi --plot butuh matplotlib: pip install matplotlib')
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.figure(figsize=(12, 4))
    plt.bar(range(256), histogram, width=1.0)
    plt.xlim(-0.5, 255.5)
    plt.xlabel('Nilai byte (0..255)')
    plt.ylabel('Frekuensi')
    plt.title('Byte histogram - %s (entropy %.4f bits/byte)' % (args.namafile, e))
    plt.tight_layout()
    plt.savefig(args.plot)
    print('Grafik disimpan ke', args.plot)
