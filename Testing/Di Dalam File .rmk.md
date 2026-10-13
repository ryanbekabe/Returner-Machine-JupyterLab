Return\[er\] Machine · format .rmk · rmh_konteks.py orde 3

# Di Dalam File .rmk

GPU List.txt berukuran **136.412 byte** menjadi **12.531 byte**. Di dalamnya tidak ada histogram dan tidak ada tabel. Isinya hanya 12 byte kepala dan satu deretan bit. Halaman ini menunjukkan dari mana deretan bit itu berasal.

## Isi file, byte demi byte

Inilah 12 byte pertama gpu.rmk dan awal kodenya, persis seperti yang tersimpan di disk.

**0 byte** untuk histogram dan konteks. Semuanya dibangun ulang oleh decoder.

Digambar sesuai skala. Pada .rmb, setiap blok 4.096 byte menyimpan histogramnya sendiri (ungu) dan rank (biru), 34 kali. Pada .rmk hanya ada satu deretan kode.

## Satu byte, satu tebakan

Setiap byte disimpan dengan cara yang sama. Contoh di bawah diambil dari file ini: setelah huruf tio, model sudah 2.877 kali melihat huruf n.

1 · lihat ke belakang"tio"

Tiga byte sebelumnya menjadi konteks.

2 · buka histogram konteksn : 2.877

Histogram ini tidak ada di file. Model membangunnya sendiri dari byte yang sudah lewat.

3 · tebakn ≈ 99,98%

Makin yakin tebakannya, makin sedikit bit yang dibutuhkan.

4 · tulis bit≈ 0,0003 bit

Byte 8 bit cukup disimpan dengan sepersekian bit di deretan kode.

### Encoder (saat menyimpan)

byte asli → model menebak → bit

lalu model belajar dari byte itu

### Decoder (saat membuka)

bit → model yang sama menebak → byte asli

lalu model belajar dari byte itu

Kalau byte belum pernah muncul di konteks itu, encoder menulis tanda **ESCAPE**, lalu mencoba konteks yang lebih pendek (2 byte, 1 byte, 0 byte). Kalau tetap tidak ada, byte itu dianggap **baru** dan butuh sekitar 8 bit.

## Coba sendiri

Ketik apa saja. Setiap kotak adalah satu byte, dan warnanya menunjukkan berapa bit yang dibutuhkan untuk menyimpannya. Pilih sebuah kotak untuk melihat langkah tebakannya. Model di sini sama persis dengan rmh_konteks.py.

Teks Orde maksimum

## Peta piksel GPU List.txt

Setiap piksel adalah satu byte dari 136.412 byte file asli, dibaca dari kiri ke kanan dan dari atas ke bawah, 512 byte per baris. Warnanya menunjukkan berapa bit yang dihabiskan byte itu di gpu.rmk. Arahkan atau ketuk peta untuk melihat byte dan teks di sekitarnya.

Latar yang terang adalah HTML berulang seperti \<option value="..." class="bl_benchmark_option\_...", yang hampir tidak butuh bit. Titik dan garis biru tua adalah angka ID dan nama GPU yang sulit ditebak. Polanya miring karena setiap baris \<option> panjangnya sedikit berbeda, sehingga posisi angka bergeser sedikit demi sedikit dari baris ke baris. Pita tipis yang lebih gelap di paling atas adalah awal file, saat model belum belajar apa-apa.

## Model belajar, blok tidak

Biaya setiap 4.096 byte di kedua format. Blok .rmb selalu mulai dari nol, jadi setiap blok membayar sekitar 2.650 byte. .rmk membayar mahal hanya di awal, lalu terus memakai apa yang sudah dipelajari.

.rmb (histogram + rank per blok).rmk (bit kode per segmen)

Lihat sebagai tabel

## Ke mana 12.519 byte kode pergi

Setiap bit di deretan kode bisa dilacak asalnya. Lebih dari separuh dipakai untuk byte yang berhasil ditebak dari 3 byte sebelumnya, meskipun rata-rata setiap byte itu hanya butuh setengah bit.

## Hasil akhir

### GPU List.txt

### logfactorial.txt

Di file ini .rmk lebih kecil dari lzma. Setelah 000, byte berikutnya hampir selalu 0, jadi deretan nol hampir tidak butuh bit.

Data dihitung dari Testing/GPU List.txt dengan rmh_konteks.py orde 3, lalu didekode ulang untuk mencatat bit setiap byte. Demo "Coba sendiri" memakai model yang sama, dan jumlah bitnya sudah dicocokkan dengan versi Python. Angka logfactorial.txt dari Testing/logfactorial.txt (zlib -9 dan lzma -9 dari Python).