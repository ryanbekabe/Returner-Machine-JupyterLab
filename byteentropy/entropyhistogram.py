import os
import sys
import math
import pefile
from collections import Counter

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
print ('Min kemungkinan ukuran file dengan asumsi efisiensi kompresi teoretis maks:')
print ((ent * fileSize), 'in bits')
print ((ent * fileSize) / 8, 'in bytes')
print ('--------------------------------')
print ()
print ('Histogramnya adalah:')
#pe = pefile.PE(namafilenya)
with open(namafilenya, "rb") as fd:
    contents = fd.read()
    c = Counter(contents)
    l = len(contents)
    d = 0
    e = 0
    i = 0
    for count in c.values():
        i += 1
        p_x = count / l
        print('Index ke -',i)
        print('Value :',count)
        d = -p_x * math.log2(p_x)		
        print(d)
        e += -p_x * math.log2(p_x)		
        if (i == len(c.values())):
                print('Len c.values() =',len(c.values()))
                print('Sum c.values() =',sum(c.values()))
                print('Min -',min(c.values()))
                print('Max -',max(c.values()))
                print('Value Counter -',c.values())
                print('Total Entropy = ', e)
    print('----')
    print(c)
    print(c.values())
