import os
import sys
import math
# 10:10 07/11/2019
# entropy.hanyajasa.com
# entropy.py 10:10 07/11/2019

if __name__ == '__main__':
    try:
        filenamearg = sys.argv[0:]
    except:
        print("Gunakan perintah: python entropy.py mybyte.bin")
        sys.exit("Proses selesai..")

for i in sys.argv[1:]:
    if ' ' in i:
        sys.argv[sys.argv.index(i)] = '"%s"' % i
namafilenya = ' '.join(sys.argv[1:])

f = open(namafilenya, "rb")
byteArr = f.read()
fileSize = len(byteArr)
f.close()
print ('Ukuran file dalam bytes:', fileSize)
print ('Memuat....')

freqList = []
freqListb = []
for b in range(256):
    ctr = 0
    for byte in byteArr:
        if byte == b:
            ctr += 1
    freqList.append(float(ctr) / fileSize)
    nilctrkei = int(ctr) / int(fileSize) * 100
    freqListb.append("%.2f" % nilctrkei)

print ('Frekuensi karakter setiap byte:')
print (freqListb)

ent = 0.0
for freq in freqList:
    if freq > 0:
        ent = ent + freq * math.log(freq, 2)
ent = -ent
print ('Shannon entropy (min bits per karakter byte):')
print (ent)
print ()
print ('Min kemungkinan ukuran file dengan asumsi efisiensi kompresi teoretis maks:')
print ((ent * fileSize), 'in bits')
print ((ent * fileSize) / 8, 'in bytes')