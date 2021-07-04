import os
import sys

# 9:18 [28,30]/09/2019
# id-ransomware.hanyajasa.com
# https://codereview.stackexchange.com/questions/62503/join-argv-list-with-spaces
# https://www.bleepingcomputer.com/forums/t/671473/stop-ransomware-stop-puma-djvu-promo-drume-help-support-topic/
# https://www.bleepingcomputer.com/forums/t/671473/stop-ransomware-stop-puma-djvu-promo-drume-help-support-topic/page-520#entry4876576
# id-ransomwared.py 6:26 17/10/2019

if __name__ == '__main__':
    try:
        #filenamearg = sys.argv[1:]
        filenamearg = sys.argv[0:]
    except:
        print("Gunakan perintah: python id-ransomware.py nufs.seto")
        sys.exit("Proses selesai..")

for i in sys.argv[1:]:
    if ' ' in i:
        sys.argv[sys.argv.index(i)] = '"%s"' % i
# args = ' '.join(sys.argv[1:])
namafilenya = ' '.join(sys.argv[1:])
#print('Nama filenya: '+namafilenya)
#print("Argumen :",chr(34),filenamearg,chr(34))
# print("Panjang Argumen :",len(sys.argv))
# print("Isi Argumen 1 :",sys.argv[0])
# print("Isi Argumen 2 :",sys.argv[1])
# print("Isi Argumen 3 :",sys.argv[2])
# print("Gabung Argumen mulai 1 :",sys.argv[0],sys.argv[1],sys.argv[2])
# print("Gabung Argumen mulai 2 :",sys.argv[1],sys.argv[2])
#filenamearg2=sys.argv[1],sys.argv[2]
#filenamearg2=chr(34),str(sys.argv[1]),str(sys.argv[2]),chr(34)
#print("filenamearg2 = ",filenamearg2)
#exit()
# f=open(filenamearg, "rb")

f=open(namafilenya, "rb")
contents = f.read()
strcontents = str(contents)

# with open(namafilenya, 'rb') as f:
    # while True:
        # buf = f.read(1024)
        # if buf: 
            # print(buf)
        # else:
            # exit()
            ## break

def stopransomware(variant,persentasi):
   print ("Kemungkinan terenkripsi variant STOP Ransomware menjadi",variant,".",persentasi," \r\n - Powered by https://HanyaJasa.Com - ")
   print (" ")
   #exit()

def pulihon(variant,persentasi):
   print ("Kemungkinan terenkripsi Ransomware menjadi",variant,"dan bisa dipulihkan dengan tingkat keberhasilan",persentasi,"(kurang lebih). Anda dapat melakukan kontak ke kami di EMail: bekabeipa@gmail.com atau di website: https://Konfirmasi.Com")
   exit()

def pulihoff(variant,persentasi):
   print ("Kemungkinan terenkripsi Ransomware menjadi",variant,"dan tidak bisa dipulihkan",persentasi,"pulih. Maaf kami tidak bisa membantu. EMail: bekabeipa@gmail.com | Website: https://Konfirmasi.Com")
   exit()

result = strcontents.find('{36A698B9-D67C-4E07-BE82-0EC5B14B4DF5}')
if (result != -1):
   print("..::",result,"::..")
   stopransomware(".STOP, .Puma, .Djvu, .Promo, .Drume, .Meds, .Seto, .Kuub, .Nesa, .Boot, .Karl, .Kvag, .Domn, .Noos, .Bora, .Peta, .Reco, .Coharos, .Cosakos,  dan lain-lain"," ")

result = strcontents.find('6se9RaIxXF9m70zWmx7nL3bVRp691w4SNY8UCir0')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".djvu* variants atau .promos atau .shadow","95%")

result = strcontents.find('D02NfEP94dKUO3faH1jwqqo5f9uqRw2Etn2lP3VB')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".rumba","95%")

result = strcontents.find('cZs3TaUYZzXCH1vdE44HNr1gnD2LtTIiSFFYv5t1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".promoz atau .promock atau .promorad","95%")

result = strcontents.find('TLuCxxAdd5BLXYWIvnjsWaCNR5lWoznhlRTSott1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".promok","95%")

result = strcontents.find('0h7mFQcjRC3pDgsRcrWZ7K7bdAgvgDosJ24DmXt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".promorad2","95%")

result = strcontents.find('upOacGl1yOz9XbrhjX9UR2M0j8i03YwVB0pXr1t1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".kroput atau .kroput1","95%")

result = strcontents.find('neFMH56G5TY6gLqHS6TpWwfIPJF1mKg4FvpeNPt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".charck","95%")

result = strcontents.find('0h7mFQcjRC3pDgsRcrWZ7K7bdAgvgDos224DmXt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".kropun","95%")

result = strcontents.find('rdSXuFaXQZ5zsBX7nzxYC2hgkTkducsD7tuV95t1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".doples atau .luces atau .luceq atau .chech","95%")

result = strcontents.find('AlMcLobh5J6wVB2Iy10guKr1kpSuFBWfXIsI6Et1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".pulsar1","95%")

result = strcontents.find('abIsuTknpjAqoGRR7OZL5HDDmc843XjBxrQOIot1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".proden","95%")

result = strcontents.find('dLoJuwk26P2wogGWZREN7JEyvljcvICqcYfwIft1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".drume atau .tronas atau .trosak atau .muslat","95%")

result = strcontents.find('sC0oYeg1wSkjbjkEwQcxTXzA0EOp8Tnc35seYQt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".grovas","95%")

result = strcontents.find('vElBnRCjG17HPbVSb8mw2WKW8uIBUDp5gbuiZat1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".grovat, .raldug","95%")

result = strcontents.find('R11Dxz37SHHVuv5otlFtzJiXUIPwPzmP6gV8gmv9')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".roland","95%")

result = strcontents.find('r77yXePcnmrctJPWrZCcbJgUlAtOa1FC9Na710t1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".etols, .guvara","95%")

result = strcontents.find('1OcNMvbG9a2vBz0BdsXRX88kjuVX9ku4EmR64St1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".norvas","95%")

result = strcontents.find('PBADSc0wL8KOzd5eGIaVThjIPeGxRqrsQgvU3qt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".moresa","95%")

result = strcontents.find('fCuKTg0kzQEXr1ewwlkMM3sl8ZzT1uEg7811p2t1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".verasto","95%")

result = strcontents.find('qn2YpOJW8NoI4X3pchKLemMVHE6hbUPemTQPlMt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".hrosas","95%")

result = strcontents.find('e4Z7Ued2uSyQfbA7vS8VKtF2dGKGH8qEQ4E1Uht1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".kiratos","95%")

result = strcontents.find('54SYshdMLwmLmgvVGWUrb336u3jYwOthqtuie5t1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".todarius","95%")

result = strcontents.find('SFOGVV9L1s8tgZVtOy4lff6n3MEgUwud5fQUdHt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".roldat","95%")

result = strcontents.find('zC2lfjIocaJoC8hWBB1yhTK2ecfIMchQ47Dkylt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".dutan","95%")

result = strcontents.find('pQseAIqgTVhPujMMiqH1ILPNUg3soGVim0NAnkt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".sarut","95%")

result = strcontents.find('nBxtbGaG4zYZQuwkRqP7d0zTIAyt6ZTtAqWL77t1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".berost","95%")

result = strcontents.find('jWOnMXbnka33AZT1RlCj0QSRbhhZHNASDvqHrDt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".forasom","95%")

result = strcontents.find('QP5YonPPBgUP0qNuS7DV82bMzke5YFYqXbRlobt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".fordan","95%")

result = strcontents.find('PTWLJBvUTDlF6G52Fs8Fmm7egqpfWrghp1m2Bot1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".codnat","95%")

result = strcontents.find('BvxonHH8kgX9meHfJweaV5ONlpO6f7IRCff0XXt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".dotmap","95%")

result = strcontents.find('mlKnUMskuvLAnwjqZpgNMoxWdYebTiuT9DMf4Vt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".ferosas","95%")

result = strcontents.find('t9hLELb8KHIC5gKnzv1k3CPJ5qpiqNZiyV5vhHt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".rectot","95%")

result = strcontents.find('JjkJ9drSkbRY2LR4ZeDjOJxCYgt4zs6svaNadvt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".skymap","95%")

result = strcontents.find('tgDlcFW2xFWyJx7JxqpZ8dNSOchUAMejoGdvf2t1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".mogera","95%")

result = strcontents.find('C1WKOJdn7siJOSKrKnoKRy5tH9aSxwMzpaUzgst1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".rezuc","95%")

result = strcontents.find('ljT0FEceXZLV8Gyhp3cCAcKbq8v85tmqMgqrVCt2')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".stone","95%")

result = strcontents.find('faLqfTl9yJBMMKsPhAv8WKbIdsFgqRtco70kHSt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".lanset","95%")

result = strcontents.find('7wlgj03aBeU43xA1mJMBMvyvGs6wERcrV31xRrt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".davda","95%")

result = strcontents.find('61K3jGfHzi5nWYLCgt3ZT7zGffHm0DNV9TGbdit1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".poret","95%")

result = strcontents.find('bDDtqPBV1xkOfMNIpmkdcyeVXG71BNezzpQwsKt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".pidon","95%")

result = strcontents.find('xUHIDCdB9IpEd1BBxXWhkitDLMP8oSzQeEYlr0t1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".heroset atau .boston","95%")

result = strcontents.find('PpzYa3nBba2MZq4MUGgxoZcZ7cbXBKtzNcipyRt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".gerosan","95%")

result = strcontents.find('3O3Zn4LeBG8kkWwS2nX61CWiHLZ46k1s632Cg9t1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".vesad","95%")

result = strcontents.find('JtkQUrpVXQB69IB5uUcXQ248Wj0DM9fjtaSThgt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".horon","95%")

result = strcontents.find('fl1QN31tuQBZKd6Q43Bemee0EycF0HBYEjwpQTt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".neras","95%")

result = strcontents.find('llb5PDChmUj6x2qLPtnlsS01VQMr9BBnhSGvh7t1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".truke","95%")

result = strcontents.find('PrHLxGQfozsYqIt6y8iByGll1cv9doSVfPSfS2t1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".dalle","95%")

result = strcontents.find('ppAG2IEqjVWKxLoaeeEd2ondL6Wu9aHAHA2NBrt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".lotep","95%")

result = strcontents.find('rZ9BMQqcE4sEMWkbGhgD1ChaoDbgM3kORd7kowt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".nusar","95%")

result = strcontents.find('iagsMxds3LxpDLrrIrIVlqmVQ2P4y09QCIrzCYt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".litar","95%")

result = strcontents.find('3OfV7t3oSHGMTLJX2O7gTxqnrYXWDDEq84VwC3t1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".besub","95%")

result = strcontents.find('MRrOmiaGsrOBV5WeKx9PFMAoug3J1vvarRjmmut1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".cezor","95%")

result = strcontents.find('l3uWOVCfd45q50p4PU204j5qPpRzALYbMPJ9Tft1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".lokas","95%")

result = strcontents.find('b0kzBppljIqs9PmJj4Y6ifw5JaTn9PNkPk9vtmt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".godes","95%")

result = strcontents.find('jkO9OpMIRJ4FHeGDM7eK5FwJTcY40YKkizu7Zgt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".budak atau .herad","95%")

result = strcontents.find('5wsxlijK7NqgKc3n9oC4xlykfU4y5YJtIQlGWJt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".berosuce atau .gehad","95%")

result = strcontents.find('68O9eTFDNbn8z2O956vweaL1v2GY5gvWBYMKcmt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".gusau atau .madek","95%")

result = strcontents.find('JAQsbdGcS17nh0dWQNvV5DXXOFilhogs4lpKitt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".tocue","95%")

result = strcontents.find('ZivCxija0GBwtwtwD0q4JRy80spT6lUyybPYhot1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".lapoi","95%")

result = strcontents.find('Q2fNGjIEoR7J8UnURFiIH13JGa23UqaNUDz4ret1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".todar","95%")

result = strcontents.find('tC9q9U9z1CHXj6ywfSklY5Ati8qfrhwcOEQpvQt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".dodoc","95%")

result = strcontents.find('qzVmsmPsBbMag5eclxPzsGPYPtD0idScDzpGvxt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".godes","95%")

result = strcontents.find('nGPslRImEtL7fKG7m94uVxPiCMecLfH3TAC0mtt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".seto","95%")

result = strcontents.find('CkRzIzWzRp3U1ooEeUkKN4owpKdqn4SHRoxPMtt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".gero atau .hese","85%")

result = strcontents.find('eXTnrcF7c7WG6gyLVibdj4JhwF6wcxk8i4YV81t1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".peta atau .moka","95%")

result = strcontents.find('Pq9d1D32xIxjAlRK7OkLl3utdbWN8syVVEm35xt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".meds","95%")

result = strcontents.find('9AGuZTsAcD5zyqTnBa8w6fa8SRmIGYbvxMuTLIt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".kvag","95%")

result = strcontents.find('YBOvIzusOa11XzxV7LAngMgmb6qJB5e90Wp0u5t1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".nesa","95%")

result = strcontents.find('Pt1u26GUozSkFJ1oZUaWXAzut6JtpGDhkrUTM5t1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".karl","95%")

result = strcontents.find('8BTjyu5e4QPLntAMA7QHz5PaV3bPWxv7090c4Gt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".kuub","95%")

result = strcontents.find('Z4aT0c1B4eHWZwaTg43eRzyM1gl3ZaaNVHrecot1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".reco","95%")

result = strcontents.find('QIho6jTmFxipRZsiUi4sllWKgMOV2pWgbnnlJAt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".noos","95%")

result = strcontents.find('hvKVwn4fNn8A1rpjC19CUFmS1ySGycmqdrz89zt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".carote","95%")

result = strcontents.find('6qLyfMFPsdHt0N7fRSGoXRvhOjNiMSIf6ovWntt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".stare","95%")

result = strcontents.find('Nk780H58ZxM4dZ5H8DRqyzWzhAZZ1G1J4gYxrtt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".cetori","95%")

result = strcontents.find('9HGTCt5KWHhAMQlcARxO5A6jkqiYUs64aMYNg3t1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".nuksus","95%")

result = strcontents.find('irtRoAwZBsG2xlRr6IAT6XJOVqA6I5bPZ0onRvt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".masodas","95%")

result = strcontents.find('AejWZezSEZGqqdJANfzMilEs9Ns6YgqnOqJDOgt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".vesrato","95%")

result = strcontents.find('98sPqhSP6fu4VGWnM1G9A075ZFxi5MMVRr2Limt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".pedro","95%")

result = strcontents.find('gyTwIW8EFRyrHBHcn0bFVHerzI3NtAa14YK0kst1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".nacro","95%")

result = strcontents.find('XIcCeHxN38dLD0Yg0cN7CdKtidQv0JQEm8hKIlt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".nasoh","95%")

result = strcontents.find('ILhWAvjUyWzsKyxDL0dKq3Su6QUUpndwXWfa2Nt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".mtogas","95%")

result = strcontents.find('ngQjbO3d7JuwM40bYYzdx9KhkhTRVvuLevPlbrt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".krusop","95%")

result = strcontents.find('JIuJ2wGghVvWM1cAKi9uwEqTSvu42tb7ooa7Rit1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".londec","95%")

result = strcontents.find('q9KuzOzkH3m0RZiU9yD24sgV2jlQpgldjv0uODt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".brusaf","95%")

result = strcontents.find('4nFS2MhU3pYPtDdwqd6UIb0hZ2RnKYsvKn5ulTt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".kovasoh atau .lotej","95%")

result = strcontents.find('gcHHxnoOwYHRVl7TXkAxlhASj14vAVxvmOWun2t1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".cosakos, atau .nvetud","95%")

result = strcontents.find('SGZBpcieKig3iLvgEDD4ATxonPIBduMgKzsfiQt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".masok","95%")

result = strcontents.find('SGZBpcieKig3iLvgEDD4ATxonPIBduMgKzsfiQt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".masok","95%")

result = strcontents.find('ivLdLLWxlGwaYapVamTFrmgK1ZxvQk2JUWsWzit1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".zatrov","95%")

result = strcontents.find('OX1w8v9Jmd3MFmBNmyayqkKHZVCmsLJUsWqShmt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".prandel","95%")

result = strcontents.find('TMO0nHR6LIOplVaj1m0fAhi7jQPCKQZq7MvRyPt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".mogranos","95%")

result = strcontents.find('4SsNNoDBzRHoERsNCDJXFi0OetZhqz2yruT2Ltt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".nelasod","95%")

result = strcontents.find('rDy9PQ5XqCEzGPAYiMtrOElRFd84gmoSzf1zJ8t1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".format","95%")

result = strcontents.find('ReORV6ShrtWNuJ0ceWs0HqhvCbzW3XJQmmwGQpt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".access","95%")

result = strcontents.find('9sbdJHqXJM4N6uliOFljF4lS1kQ5MipUBQqeGet1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".ndarod","95%")

result = strcontents.find('qzVmsmPsBbMag5eclxPzsGPYPtD0idScDzpGvxt1')
if (result != -1):
   print("..::",result,"::..")
   pulihon(".bopador atau .novasof","95%")


result = strcontents.find('a7L11fXuA1KkZ677FZb2EKplJm3lTrCaF2F7C8xP')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".karl online","0%")

result = strcontents.find('qPqAltpQwSdHieAtVcpXON8z0ye0GCrzeeKQuAzl')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".kuub online","0%")

result = strcontents.find('djeU3RU17SLDCDhYn5AywxzSgDmUyzMd4SIzTkXk')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".kuub online","0%")

result = strcontents.find('Z9c1WzcY5IJueZCGwKxRZuqdP0kYmMgyxSw5mpmB')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".kuub online","0%")

result = strcontents.find('vhCfosuNzcVxKZgUtZqA7dsCGpFq6MtiIJSWVZOj')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".kuub online","0%")

result = strcontents.find('4tRFXKVtMY6MnbspiqMI3rij3HFCnBdt7G47xuFe')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".nesa online","0%")

result = strcontents.find('BGDV4OBSN5wxJRmV93289uXfvwGHtS9MGng1U6mn')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".meds online","0%")

result = strcontents.find('dpjzypUapAxpeiQ1SbwPzhD9qyMjvSZXepCGGFnc')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".boot online","0%")

result = strcontents.find('8NVKNXZHUic3LpPpeITsGhdQzZhi86cMNE8jfSC9')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".meds online","0%")

result = strcontents.find('sVaFgCWbWlmMFVi5w74AjYJgFM21uMTU6zOPoWJO')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".kuub online","0%")

result = strcontents.find('T5p7u9B6EwRD11H3EwQ6mTMTItjCLjEsJbccT9UE')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".nesa online","0%")

result = strcontents.find('slk7LOJueJ89lpzyW6U084no3S2i0Jd5tPA8DcB6')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".nesa online","0%")

result = strcontents.find('QykRaBSeb70fkAd9Ws5GluoJvJnTzsyeW8o5Qnzc')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".boot online","0%")

result = strcontents.find('nV77cEjl2X8E5HeAIv4E9MLUyD9hTughURcyG7vs')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".nesa online","0%")

result = strcontents.find('Sl4vvx5qC0HQNyV67Oe1xVQwv0cuyDAyZQnAies7')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".kvag online","0%")

result = strcontents.find('KmuqYtqf11t2bTnzVs8ToI68sd1cajQb73QaXhrf')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".kvag online","0%")

result = strcontents.find('rHf6SWUkOM7w5EVVrXU347OeNyLyYHMCzKPKBBSC')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".kuub online","0%")

result = strcontents.find('qnRlHMZT49zSlA9kSG7YK0a2iBd3UTIPWFySXUjZ')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".hese online","0%")

result = strcontents.find('qLYgtlynVHEM3sgkspEUEIAKN1QO7M9cCGxD4Bt1')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".domn offline","0%")

result = strcontents.find('IriPUKWyGg4nOREHyk3RZHOUiQGeOJsMjnmK8fbB')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".kuub online","0%")

result = strcontents.find('jYYm7ah2Fz0pIKPxLLbTxZdlT3eDvPgkAGJs7eRM')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".domn online","0%")

result = strcontents.find('UEQHHulMGTAEkmPkRGXGrajMhNRkpK5TDkFvWw8J')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".kuub online","0%")

result = strcontents.find('8rqrTYeNADP37JgWhU1Z7AQZ2If5byoIVvpbcYxF')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".kuub online","0%")

result = strcontents.find('yEd2q3hj9ETBCJGfwxOnDOJEcvmyUeP0UulsTKmS')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".nesa online","0%")

result = strcontents.find('DzL6Fq3LSnb3WwA3u2bcHWcSvtefsQLSXp6dCWVu')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".kvag online","0%")

result = strcontents.find('IiwzAUQSSmkSRkPNFVms5fD8qNNbHLVha1xdnzrh')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".kuub online","0%")

result = strcontents.find('QGK57I5JbjOGT6dOG2ePSVvKaOml0ipKhTPZjU3H')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".karl online","0%")

result = strcontents.find('YMpHKYRJjoQVDXiH8L7pZ9OKE7lUALBvD8VjllVm')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".noos online","0%")

result = strcontents.find('baFvtCiTEbgbQ3WsRuMzmQOXDb1kFifi8B7hoOVs')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".kvag online","0%")

result = strcontents.find('0kmZDy0JoUuiZwykHQZ9d8xtezBEVj98f2FGywPg')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".noos online","0%")

result = strcontents.find('NU9EiXNGWyCl155Day4aIK8GMoSrdb3IJtoWjKEL')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".noos online","0%")

result = strcontents.find('5PgpqzSRFybNF0LZtqlVNz33TBxgWe7qo9cu9Nt1')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".bora","95%")

result = strcontents.find('rQ7WUgrlL16OuWSN1t75J6qgcdpKOTxmGf20SyBc')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".nesa online","0%")

result = strcontents.find('kL6vyDOr74ik6GBbNLx00iu8RpbzVOeRkHyCLX47')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".bora online","0%")

result = strcontents.find('cKrNepCfhnyvmJ956kfEGYtFfEf9nCKDuo5qQYLh')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".bora online","0%")

result = strcontents.find('cUnLXmE8nHD9UIkcWMs3qeGPlFtNYfx7zQvlSREU')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".bora online","0%")




result = strcontents.find('B93J12')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".money admin at stex777.com","0%")

result = strcontents.find('U9NROL')
if (result != -1):
   print("..::",result,"::..")
   pulihoff(".pdf 3442516480 at qq.com","0%")


# print(result)
if (result == -1):
   print ("Maaf, file tidak teridentifikasi. Kemungkinan terkena Ransomware baru atau terenkripsi oleh Ransomware dengan keadaan komputer terkoneksi ke internet.")
   exit()
