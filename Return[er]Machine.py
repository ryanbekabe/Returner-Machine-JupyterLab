# import os
import sys
import cv2
import math
import struct
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from collections import Counter
import itertools

print('Time: ',datetime.now())
def start_end_timer(start_time=None):
    if not start_time:
        start_time = datetime.now()
        return start_time
    elif start_time:
        thour, temp_sec = divmod((datetime.now() - start_time).total_seconds(), 3600)
        tmin, tsec = divmod(temp_sec, 60)
        print('\nTime taken: %i hours %i minutes and %s seconds.' % (thour, tmin, round(tsec, 2)))

start_time = start_end_timer(None)

varmax = 256
vardes = 0
vardtm = ''
freqListHisto = []
freqListHistoi = []
arrListDat = []
arrListDat2 = []
arrListDatb = []
arrasc = []
freqList = []
freqListb = []
bitkei = 0
byten = 0
bytefrmtarrn = 0
bytefrmtarrv = 0
bytefrmtarrna = 0
bytefrmtarrvb = 0
c = 0

namafilenya = 'bismillah.txt'
f = open(namafilenya, 'rb')
byteArr = f.read()
fileSize = len(byteArr)
f.close()

valrand = byteArr
randomByteArray = bytearray(valrand)
flatNumpyArray = np.array(randomByteArray)

lnfile = len(str(fileSize))

#print('----freq_List_Histogramnya----')
for b in range(256):
    #print('b=>',b)
    ctr = 0
    for byte in randomByteArray:
        if b==255:
            #listDat = [1,1,3,4] #data perm harus urut
            #listDtt = (1,3,1,4) #data asli dibiarkan acak
            byten = byten + 1
            #zfillbyten = (int(fileSize)/256)+2
            #zfillbytenb = "%.0f" % zfillbyten
            #print('zfillbyten=>',zfillbytenb)
            #print(str(byten).zfill(lnfile),'byte = v.0-255 =',byte)
            if byte > 127:
                bytefrmtarrn = byte-128
                bytefrmtarrv = bytefrmtarrn-128
                print('=>',bytefrmtarrv)
                print(str(byten).zfill(lnfile),'byte = v.0-255 =',byte,'=>',bytefrmtarrv)
                arrListDat.append(bytefrmtarrv)
            else:
                print(str(byten).zfill(lnfile),'byte = v.0-255 =',byte)
                arrListDat.append(byte)
                #print(arrListDat)
                #print(len(arrListDat))
                #n-128=v,v-128=v2;
            #perm = itertools.permutations(listDat)
            #for i in set(perm):
            #    c = c + 1
            #    print(c,i)

            #print(str(byten).zfill(int(zfillbytenb)),'byte = value ke dari 0-255 :',byte)
            #continue;
            #break;
        if byte == b:
            ctr += 1
    nilctrkei = int(ctr) / int(len(randomByteArray)) * 100
    nilctrkeib = bitkei, int(ctr)
    anaktangga = ''
    if(int(ctr)) == 0:
        #print('->',str(bitkei).zfill(3))
        #continue;
        pass
    else:
        for summuncul in range(0,int(ctr)):
            anaktangga = anaktangga + '|'
            if(ctr / (summuncul + 1) == 1):
                #print("=> %s : %s" % (str(bitkei).zfill(3), anaktangga))
                #continue;
                pass
    freqList.append("%.2f" % nilctrkei)
    freqListb.append(nilctrkeib)
    freqListHisto.append(ctr)
    bitkei += 1
print(namafilenya,"=",len(arrListDat))
print('Origin arrListDat:',arrListDat)
#print('arr ke-0=>',arrListDat[0])
#print('arr ke-1=>',arrListDat[1])
#static_sort_arr()
#static_num.x = arrListDatb.sort()
arrListDatb = arrListDat
arrListDatb.sort()
print('Sorted arrListDat:', arrListDatb)

tmpflsort = str(namafilenya) + str('.tmp')
ftmpflsort = open(tmpflsort,'w')
ftmpflsort.write(str(arrListDatb))
ftmpflsort.close()

ftmpflsort = open(tmpflsort, 'r')
vartmpflsort = ftmpflsort.read()
#print('vartmpflsort=>',vartmpflsort)
#print('vartmpflsort=>',vartmpflsort)
#print('arr ke-0=>',arrListDatb[0])
#print('arr ke-1=>',arrListDatb[1])
#static_sort_arr()
#print('static_num.x=>',static_num.x)
#print('Origin arrListDat:',arrListDat)
#print('arr ke-0=>',arrListDat[0])
#print('arr ke-1=>',arrListDat[1])
vartmpflsortmod1 = str(vartmpflsort)[1:-1]
vartmpflsortmod2 = "(" + vartmpflsortmod1 + ")"
#print('vartmpflsortmod2=>',vartmpflsortmod2)
#res = str(test_list)[1:-1]
perm = itertools.permutations(arrListDatb)
#print('Yang jadi Perm=>',arrListDatb)

f2 = open(namafilenya, 'rb')
byteArr2 = f2.read()
fileSize = len(byteArr2)

ByteArray2nya = bytearray(byteArr2)
flatNumpyArray2 = np.array(ByteArray2nya)
#print('flatNumpyArray2=>',flatNumpyArray2)
for byte in flatNumpyArray2:
    if byte > 127:
        bytefrmtarrna = byte-128
        bytefrmtarrvb = bytefrmtarrna-128
        arrListDat2.append(bytefrmtarrvb)
    else:
        arrListDat2.append(byte)
#print('append_arrListDat2=>',arrListDat2)
vartmpflsortmod1a = str(arrListDat2)[1:-1]
vartmpflsortmod2b = "(" + vartmpflsortmod1a + ")"
#print('append_arrListDat2b=>',vartmpflsortmod2b)
n = fileSize
fact = 1
for i in range(1,n+1):
    fact = fact * i
#print ("The factorial of 23 is : ",end="")
#print (fact)
#for i in list(perm):
for i in set(perm):
    c = c + 1
    #if c == 1:
    #print(str(byten).zfill(lnfile)
    #print(str(c).zfill(len(str(fact))),i)
    #print(c,i)
    #print('i=>',i)
    #print('vartmpflsortmod2,i=>',vartmpflsortmod2,i)
    #print('arrListDatb == arrListDat=>',arrListDatb,arrListDat)
    #print("if str(vartmpflsortmod2) == str(i)=>|")
    #print('Yang jadi tetap=>',vartmpflsortmod2b)
    if str(vartmpflsortmod2b) == str(i):
        #print('untuk Sama indeks ke - arrListDatb=>',arrListDatb)
        #print('untuk Sama indeks ke - i=>',i)
        #print('str(vartmpflsortmod2)=>',str(vartmpflsortmod2))
        #print('str(i)=>',str(i))
        print('Sama indeks ke -',c)
        break;
        #pass;
        #continue;

f2.close()
ftmpflsort.close()
#print('Origin arrListDat:',arrListDat)
#perm = itertools.permutations(listDat)

print('----0-255 / 00-FF----')
#print (freqListb)

filefreqList0 = str(namafilenya) + str('.storetohash')
ffilefreqList0 = open(filefreqList0,'a')
ffilefreqList0.close()

filefreqList = str(namafilenya) + str('.storetohash')
ffilefreqList = open(filefreqList,'w')
ffilefreqList.write(str(freqListb))
ffilefreqList.close()

print('----.----')
print ('Frequencies of each byte-character:')
#print (freqList)
print('----..----')
contents = randomByteArray
c = Counter(contents)
l = len(contents)
d = 0
e = 0
i = 0
for count in c.values():
   i += 1
   p_x = count / l
   d = -p_x * math.log2(p_x)
   e += -p_x * math.log2(p_x)
   if (i == len(c.values())):
      print('Len c.values() =',len(c.values()))
      print('Sum c.values() =',sum(c.values()))
      print('Min -',min(c.values()))
      print('Max -',max(c.values()))
      print('Total Entropy = ', e)
print('----Values----')
print(c)
for vardes in range(varmax):
    freqListHistoi.append(vardes)
names = freqListHistoi
values = freqListHisto
plt.bar(names, values)
plt.suptitle('Byte Histogram: ' + namafilenya + ', (' + str(fileSize) + ' bytes)')
fig1 = plt.gcf()
#plt.show()
#plt.draw()
#fig1.savefig(namafilenya + '.png', dpi=100)
fig1.savefig(namafilenya + '.png', density=0)
print('Time: ',datetime.now())
start_end_timer(start_time)