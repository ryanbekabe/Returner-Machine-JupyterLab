
Return[er] Machine - November 2019, Juli 2021

Return[er] Machine, begitu saya menyebutnya, adalah sebuah mesin kompresi gabungan, yang bersifat seperti program kompresi dan serta hash sekaligus.
Dikatakan kompresi karena memperkecil ukuran file aslinya menjadi bentuk DNA hash, dan dikatakan hash karena hashnya sendiri merupakan nilai ukuran file DNA yang tetap seperti halnya hash SHA512 misalnya, yang dari hash tersebut lah akan diciptakan kembali file dengan ukuran aslinya menggunakan teknik Permutasi (untuk saat ini, dan masih terlalu boros terhadap sumberdaya komputer).

## Setup

Butuh Python 3.10 atau lebih baru.

```bash
# 1. Buat virtual environment
python -m venv .venv

# 2. Aktifkan
#    Windows (PowerShell):  .venv\Scripts\Activate.ps1
#    Linux/macOS:           source .venv/bin/activate

# 3. Install dependensi inti
pip install -r Testing/requirements.txt

# (Opsional) TensorFlow/Keras/CuPy untuk numba-cuda-stencil.ipynb, butuh GPU NVIDIA + CUDA
pip install -r Testing/requirements-optional.txt

# 4. Jalankan JupyterLab
jupyter lab
```

Menjalankan script Python langsung, misalnya:

```bash
cd Testing
python "Return[er]Machine.py"             # input diatur lewat variabel namafilenya di dalam script
cd ..
python byteentropy/histogram_v2.py <nama_file>
```

## Byte Histogram & Byte Entropy (`byteentropy/`)

| Script | Fungsi |
|---|---|
| `entropy.py` | Frekuensi tiap byte (dalam persen) + Shannon entropy |
| `histogram.py` | Histogram + entropy (versi lama, lihat catatan di bawah) |
| `entropyhistogram.py` | Sama dengan `histogram.py` |
| `histogram_v2.py` | **Perbaikan** `histogram.py`, versi yang disarankan |
| `permutasi_rank.py` | Enumerative coding: menyimpan data sebagai histogram + rank, lalu menyusunnya kembali (lihat bagian [Enumerative Coding](#enumerative-coding-histogram--rank)) |
| `rmh.py` | Encode file ke `.rmh` (histogram + rank) dan decode kembali (lihat bagian [Format File .rmh](#format-file-rmh-simpan-ke-file)) |
| `rmh_blok.py` | Versi per blok dari `rmh.py`: cepat untuk file besar dan bisa paralel (lihat bagian [Per Blok](#per-blok-file-rmb)) |
| `rmh_adaptif.py` | Histogram dipelajari dari data yang sudah terbuka, tidak disimpan (lihat bagian [Histogram Adaptif](#histogram-adaptif-file-rma)) |
| `rmh_konteks.py` | Satu histogram adaptif per konteks (PPM), menebak byte dari byte-byte sebelumnya (lihat bagian [Konteks PPM](#konteks-ppm-file-rmk)) |
| `rmh_konteks_info.py` | Melihat isi file `.rmk`: rincian per segmen, ke mana bit dihabiskan, konteks yang dipelajari, dan jejak decode (lihat bagian [Melihat Isi File .rmk](#melihat-isi-file-rmk)) |
| `rmh_final.py` | Memilih mode terbaik secara otomatis (konteks orde 1..5, adaptif, atau mentah) dan menyimpan SHA-256 sebagai sidik jari (lihat bagian [Return[er] Machine Final](#returner-machine-final-file-rmf)) |
| `rmh_final2.py` | **Versi yang disarankan.** Seperti `rmh_final.py`, ditambah mode campuran per blok: bagian yang sudah terkompresi (gambar, ZIP) disimpan mentah, hanya bagian berpola yang dikodekan. Jauh lebih cepat untuk PDF dan file campuran (lihat bagian [Mode Campuran per Blok](#mode-campuran-per-blok-rmf-versi-2)) |

### Istilah ekstensi file

Awalan **rm** berasal dari **R**eturner **M**achine. Huruf terakhir menunjukkan tahap pengembangan: Hash → Blok → Adaptif → Konteks → Final.

| Ekstensi | Singkatan | Penanda (4 byte pertama) | Program | Cara menyimpan |
|---|---|---|---|---|
| `.rmh` | Return[er] Machine **H**ash | `RMH1` | `rmh.py` | Satu histogram + satu rank untuk seluruh file. Lihat [Format File .rmh](#format-file-rmh-simpan-ke-file) |
| `.rmb` | Return[er] Machine **B**lok | `RMB1` | `rmh_blok.py` | File dipecah per blok, setiap blok punya histogram + rank sendiri. Lihat [Per Blok](#per-blok-file-rmb) |
| `.rma` | Return[er] Machine **A**daptif | `RMA1` | `rmh_adaptif.py` | Histogram tidak disimpan, tetapi dipelajari dari byte yang sudah terbuka. Lihat [Histogram Adaptif](#histogram-adaptif-file-rma) |
| `.rmk` | Return[er] Machine **K**onteks | `RMK1` | `rmh_konteks.py` | Satu histogram adaptif untuk setiap konteks (1..N byte sebelumnya). Lihat [Konteks PPM](#konteks-ppm-file-rmk) |
| `.rmf` | Return[er] Machine **F**inal | `RMF1`, `RMF2` | `rmh_final.py` (versi 1), `rmh_final2.py` (versi 2) | Mode terbaik dipilih otomatis + SHA-256 file asli. Versi 2 menambah mode campuran per blok. `rmh_final2.py` bisa membuka kedua versi. Lihat [Return[er] Machine Final](#returner-machine-final-file-rmf) dan [Mode Campuran per Blok](#mode-campuran-per-blok-rmf-versi-2) |

Penanda di awal file membuat program bisa mengenali formatnya. Angka `1` adalah nomor versi format, sehingga format yang diubah di masa depan bisa memakai `RMK2` dan seterusnya tanpa merusak file lama.

**Ukuran hasil mengikuti informasi baru, bukan ukuran file.** Contoh `.rmk` orde 3:

| Jenis data | 1.000 byte | 10.000 byte | 100.000 byte |
|---|---|---|---|
| Semua nol (`0x00`) | 14 | 14 | 18 |
| `bismillah ` berulang | 28 | 30 | 34 |
| `GPU List.txt` (potongan awal) | 308 | 1.113 | 9.243 |
| Data acak | 1.137 | 11.087 | 110.019 |

Data yang berulang hampir tidak bertambah. Data berpola tumbuh lebih lambat dari file aslinya. Data acak tumbuh seiring ukuran file, bahkan sekitar 10% lebih besar karena biaya ESCAPE. Untuk data acak berukuran besar, `.rma` lebih cocok (101.001 byte untuk 100.000 byte acak).

### Konsep singkat

- Satu byte = 8 bit, jadi ada 2⁸ = **256 kemungkinan nilai, yaitu 0 sampai 255**.
- **Byte histogram** = berapa kali tiap nilai byte 0..255 muncul di dalam file (256 angka frekuensi).
- **Byte entropy (Shannon)** = **satu angka** yang dihitung dari histogram tersebut:

  `H = -Σ p(i) · log2 p(i)`, dengan `p(i) = frekuensi(i) / ukuran file`

  Nilainya 0 sampai 8 bit per byte. 0 berarti isi file hanya satu nilai byte (misalnya `Testing/nullbyte.txt`). 8 berarti semua nilai byte muncul merata (data acak, terenkripsi, atau sudah terkompresi).
- `H × ukuran_file / 8` = batas bawah teoretis ukuran hasil kompresi (dalam byte), jika tiap byte dikompresi secara independen.

### Perbaikan pada `histogram_v2.py`

`histogram.py` dan `entropy.py` tidak diubah. Perbaikan dibuat sebagai file terpisah:

1. **Index = nilai byte (0..255).** Di `histogram.py`, `Index ke - i` hanya nomor urut kemunculan dari `Counter`, bukan nilai byte-nya.
2. **Semua 256 nilai byte bisa ditampilkan** (opsi `--semua`), termasuk yang frekuensinya 0.
3. Tabel menampilkan nilai byte, hex, karakter, frekuensi, persen, dan kontribusi `-p·log2(p)` tiap byte.
4. **Nama file berspasi didukung.** `histogram.py` menambahkan tanda kutip ke nama file sehingga file gagal dibuka.
5. Ada pesan error yang jelas untuk file yang tidak ada atau kosong.
6. Opsi `--plot` menyimpan grafik histogram ke PNG (butuh `matplotlib`).

### Cara pakai

```bash
python byteentropy/histogram_v2.py <nama_file> [--semua] [--plot <file.png>]
```

| Opsi | Keterangan |
|---|---|
| `<nama_file>` | File yang akan dianalisis (wajib) |
| `--semua` | Tampilkan juga byte yang frekuensinya 0 (total 256 baris) |
| `--plot <file.png>` | Simpan grafik histogram ke file PNG |
| `-h`, `--help` | Tampilkan bantuan |

Contoh:

```bash
python byteentropy/histogram_v2.py Testing/bismillah.txt
python byteentropy/histogram_v2.py Testing/bismillah.txt --semua
python byteentropy/histogram_v2.py "Testing/nama file berspasi.bin" --plot histogram.png
```

Contoh output untuk `Testing/bismillah.txt`:

```
Ukuran file dalam bytes: 9

Histogramnya adalah:
 Byte  Hex  Char    Frekuensi    Persen   -p*log2(p)
   97   61     a            1  11.1111%     0.352214
   98   62     b            1  11.1111%     0.352214
  104   68     h            1  11.1111%     0.352214
  105   69     i            2  22.2222%     0.482206
  108   6C     l            2  22.2222%     0.482206
  109   6D     m            1  11.1111%     0.352214
  115   73     s            1  11.1111%     0.352214
----
Jumlah nilai byte berbeda yang muncul = 7 dari 256
Total byte (sum frekuensi)            = 9
Frekuensi min (yang muncul)           = 1
Frekuensi max                         = 2

Shannon entropy (bits per byte, 0..8) = 2.725480556997868
Min kemungkinan ukuran file dengan asumsi efisiensi kompresi teoretis maks:
24.529325012980813 in bits
3.0661656266226016 in bytes
```

Nilai entropy di atas sama dengan hasil `entropy.py` untuk file yang sama.

## Enumerative Coding (Histogram + Rank)

Script: `byteentropy/permutasi_rank.py`

### Masalah: permutasi menghasilkan data kembar

Histogram hanya mencatat **berapa kali** tiap byte muncul, tanpa **urutannya**. Akibatnya banyak data berbeda punya histogram yang sama. Jumlahnya dihitung dengan permutasi multiset:

```
jumlah susunan = n! / (c1! · c2! · ... · ck!)
```

`n` = panjang data, `c1..ck` = frekuensi tiap nilai byte.

Contoh `bismill` (b=1, i=2, l=2, m=1, s=1), panjang 7 byte:

```
7! / (2! · 2!) = 1.260 susunan
```

`bismill`, `ismillb`, `lilsmib`, dan seterusnya punya histogram yang identik. Permutasi saja tidak bisa menentukan mana yang asli.

### Percobaan: memberi tanda posisi awal dan akhir

| Tanda | Kandidat tersisa |
|---|---|
| tanpa tanda | 1.260 |
| awal `b` + akhir `l` | 60 |
| awal `bi` + akhir `ll` | 6 |
| awal `bis` + akhir `ill` | 1 |

Kandidat baru tinggal 1 setelah 6 dari 7 byte ditandai. Itu sama saja dengan menyimpan data aslinya, jadi tanda posisi tidak efisien.

### Solusi: simpan nomor urut permutasi (rank)

Semua susunan diurutkan secara leksikografis berdasarkan nilai byte 0..255 dan diberi nomor mulai dari 0. Yang disimpan adalah **histogram + nomor urut (rank)** data asli.

Contoh kecil, data `aab` (a=2, b=1), ada 3!/2! = 3 susunan:

| Rank | Susunan |
|---|---|
| 0 | `aab` |
| 1 | `aba` |
| 2 | `baa` |

Jadi `aab` cukup disimpan sebagai histogram `{a:2, b:1}` + rank `0`.

Hasil untuk data di repo ini:

| Data | Total susunan | Rank | Bit untuk rank |
|---|---|---|---|
| `bismill` | 1.260 | 57 | 11 bit |
| `ismillb` | 1.260 | 533 | 11 bit |
| `bismillah` | 90.720 | 15.094 | 17 bit |

`bismill` dan `ismillb` punya histogram sama tetapi rank berbeda, sehingga keduanya bisa dibedakan dengan pasti.

### Cara kerja algoritma

**Encode (data → rank)**, untuk tiap posisi dari kiri ke kanan:

1. Untuk setiap nilai byte yang **lebih kecil** dari byte di posisi ini dan masih tersisa di histogram, tambahkan ke rank jumlah susunan yang diawali byte tersebut: `total × c[b] / sisa`.
2. Kurangi frekuensi byte di posisi ini, lalu lanjut ke posisi berikutnya.

**Decode (histogram + rank → data)**, untuk tiap posisi:

1. Telusuri nilai byte dari kecil ke besar. Hitung jumlah susunan yang diawali byte tersebut (`blok`).
2. Jika `rank < blok`, byte itulah yang dipakai di posisi ini. Jika tidak, kurangi rank dengan `blok` dan coba byte berikutnya.

Decode menghitung byte yang tepat langsung di setiap posisi. Susunan lain **tidak perlu dibangkitkan satu per satu** (tanpa brute force). Perhitungannya memakai bilangan bulat Python yang presisinya tak terbatas, jadi rank tetap tepat walaupun angkanya sangat besar.

### Cara pakai

```bash
python byteentropy/permutasi_rank.py <nama_file>
python byteentropy/permutasi_rank.py --teks <teks>
```

| Opsi | Keterangan |
|---|---|
| `<nama_file>` | File yang akan diproses |
| `--teks <teks>` | Gunakan teks (UTF-8) sebagai data, sebagai pengganti file |
| `-h`, `--help` | Tampilkan bantuan |

Contoh:

```bash
python byteentropy/permutasi_rank.py --teks bismill
python byteentropy/permutasi_rank.py Testing/bismillah.txt
```

Contoh output:

```
Data                  : bismill
Ukuran                : 7 byte = 56 bit
Histogram             : b=1, i=2, l=2, m=1, s=1

Kandidat permutasi tersisa jika posisi tertentu ditandai:
Tanda                                          Kandidat
tanpa tanda                                        1260
awal "b" + akhir "l"                                 60
awal "bi" + akhir "ll"                                6
awal "bis" + akhir "ill"                              1

Total permutasi        : 1260
Rank (nomor urut)      : 57
Bit untuk rank         : 11 bit
Batas Shannon n*H      : 15.65 bit

Decode dari histogram + rank: bismill -> SAMA PERSIS dengan data asli
```

Script selalu melakukan encode lalu decode, kemudian membandingkan hasilnya dengan data asli. Pengujian dilakukan pada `bismill`, `ismillb`, `Testing/bismillah.txt`, `Testing/nullbyte.txt`, dan 50 data biner acak. Semuanya kembali sama persis.

### Batasan

- **Histogram juga harus disimpan.** Untuk data kecil, biaya histogram lebih besar dari datanya. `bismill` punya 5 nilai byte berbeda: pasangan (nilai, jumlah) butuh sekitar 10 byte, ditambah 11 bit rank, lebih besar dari 7 byte aslinya.
- **Untuk data besar**, ukuran histogram + rank mendekati batas Shannon `n × H`. Hasilnya setara dengan kompresi entropi orde-0 (misalnya arithmetic coding) dan tidak bisa lebih kecil dari batas itu.
- **Data acak** (entropy ≈ 8 bit/byte) menghasilkan rank yang ukurannya hampir sama dengan data aslinya, jadi tidak ada penghematan.
- Untuk data besar, encode/decode melambat karena operasi bilangan bulat besar. Script memberi peringatan untuk data di atas 100.000 byte.
- `permutasi_rank.py` hanya mendemonstrasikan encode → decode di memori. Untuk menyimpan ke file, gunakan `rmh.py` (bagian berikut).

## Format File .rmh (Simpan ke File)

Script: `byteentropy/rmh.py`. Script ini melanjutkan `permutasi_rank.py`: histogram + rank disimpan ke file `.rmh`, lalu file asli disusun kembali dari file `.rmh` tersebut.

### Cara pakai

```bash
python byteentropy/rmh.py encode <file>       [-o <file.rmh>]   # file asli -> .rmh
python byteentropy/rmh.py decode <file.rmh>   [-o <file_hasil>] # .rmh -> file asli
python byteentropy/rmh.py info   <file.rmh>                     # lihat isi .rmh
```

| Perintah | Keterangan | Nama output default |
|---|---|---|
| `encode` | Membuat file `.rmh` dan menampilkan perbandingan ukuran dengan zlib, lzma, dan batas Shannon | `<file>.rmh` |
| `decode` | Menyusun kembali file asli, lalu memverifikasi dengan CRC32 | `<file tanpa .rmh>.decoded` |
| `info` | Menampilkan ukuran asli, CRC32, total permutasi, rank, dan histogram | - |

Contoh lengkap:

```bash
python byteentropy/rmh.py encode Testing/bismillah.txt -o bismillah.rmh
python byteentropy/rmh.py info bismillah.rmh
python byteentropy/rmh.py decode bismillah.rmh -o bismillah_kembali.txt
```

Output `encode`:

```
Rincian file .rmh:
  header              6 byte
  histogram          14 byte
  crc32               4 byte
  rank                3 byte
  TOTAL              27 byte

Perbandingan ukuran:
  asli                  9 byte
  .rmh                 27 byte  (300.0% dari asli)
  zlib -9              17 byte  (188.9% dari asli)
  lzma -9              68 byte  (755.6% dari asli)
  n*H/8               3.1 byte  (batas Shannon orde-0, n*H/8)
```

### Struktur file

Angka bertanda *varint* disimpan dengan LEB128: 7 bit per byte, bit tertinggi menandakan masih ada byte lanjutan. Angka kecil (< 128) cukup 1 byte.

| Bagian | Ukuran | Isi |
|---|---|---|
| Magic | 4 byte | `RMH1`, penanda file `.rmh` |
| n | varint | Ukuran file asli dalam byte |
| k | varint | Jumlah nilai byte berbeda (0..256) |
| Histogram | k × (1 byte + varint) | Pasangan (nilai byte, frekuensi), urut naik |
| CRC32 | 4 byte | Checksum file asli untuk verifikasi decode |
| Rank | m byte | Nomor urut permutasi, big-endian |

Panjang rank `m` **tidak disimpan**. Decoder menghitung total permutasi dari histogram, lalu `m` = jumlah byte yang dibutuhkan untuk menampung `total − 1`.

Contoh isi `bismillah.rmh` (27 byte):

```
52 4D 48 31                 magic "RMH1"
09                          n = 9
07                          k = 7
61 01 62 01 68 01 69 02     a=1 b=1 h=1 i=2
6C 02 6D 01 73 01           l=2 m=1 s=1
A9 42 0C 61                 CRC32
00 3A F6                    rank = 15094
```

### Verifikasi saat decode

`decode` menolak file yang rusak dengan pesan yang jelas:

| Kerusakan | Pesan |
|---|---|
| Bukan file `.rmh` | `Bukan file .rmh (magic tidak cocok)` |
| File terpotong | `Panjang rank tidak sesuai (...)` |
| Isi rank/histogram berubah | `CRC32 tidak cocok, hasil decode rusak` |
| Jumlah frekuensi ≠ n | `Jumlah frekuensi histogram tidak sama dengan ukuran file` |

### Hasil uji pada file di repo

Semua file di bawah ini kembali **identik byte per byte** setelah encode → decode (dicek dengan `cmp`):

| File | Asli | .rmh | zlib -9 | lzma -9 | n·H/8 |
|---|---|---|---|---|---|
| `Testing/bismillah.txt` | 9 | 27 | 17 | 68 | 3,1 |
| `Testing/nullbyte.txt` | 256 | 14 | 12 | 72 | 0 |
| `Testing/HoRM.txt` | 4.690 | 2.243 | 1.236 | 1.024 | 2.158,9 |
| `Testing/Return[er]Machine.py` | 7.235 | 4.576 | 2.103 | 2.168 | 4.429,8 |
| `Testing/RMHash_HoRM2.txt` | 8.585 | 4.043 | 1.146 | 584 | 3.987,0 |
| `Testing/123.txt.png` | 10.073 | 10.287 | 8.369 | 8.264 | 9.883,8 |
| `Testing/Return[er]Machine-NestedRubik256DNA.py` | 15.112 | 15.005 | 12.354 | 12.208 | 14.603,2 |

(ukuran dalam byte)

Selain itu, 300 data acak (termasuk file kosong dan ke-256 nilai byte) juga lolos uji encode → decode.

### Membaca hasilnya

- **`.rmh` selalu mendekati n·H/8**, sesuai teori enumerative coding. Rank sendiri sedikit lebih kecil dari n·H/8. Selisih kecil di atasnya berasal dari header, histogram, dan CRC32.
- **zlib dan lzma lebih kecil** pada file teks karena keduanya memanfaatkan **urutan dan pengulangan** (kata, baris yang mirip). Enumerative coding orde-0 hanya memakai frekuensi tiap byte. Contohnya `RMHash_HoRM2.txt` yang sangat berulang: lzma 584 byte, sedangkan `.rmh` 4.043 byte.
- **File yang sudah terkompresi** seperti PNG tidak bisa diperkecil, bahkan sedikit membesar karena tambahan header + histogram.
- **File sangat kecil** membesar karena biaya header + histogram + CRC32 (minimal 10 byte).

### Kecepatan

| Ukuran file | Encode | Decode |
|---|---|---|
| 4,7 KB | 0,02 detik | 0,03 detik |
| 15 KB | 0,44 detik | 0,59 detik |
| 50 KB | 3,0 detik | 3,8 detik |

Waktu naik kira-kira kuadratik terhadap ukuran file, karena rank adalah satu bilangan bulat raksasa yang ikut dihitung ulang di setiap posisi. Script memberi peringatan untuk file di atas 20.000 byte. Solusinya adalah memecah file per blok, lihat bagian [Per Blok](#per-blok-file-rmb).

## Per Blok (File .rmb)

Script: `byteentropy/rmh_blok.py`. Script ini melanjutkan `rmh.py`: file dipecah menjadi blok-blok berukuran tetap (default 4.096 byte), dan **setiap blok disimpan sebagai histogram + rank sendiri**. `rmh.py` tidak diubah. `rmh_blok.py` memakai fungsi `rank`/`unrank` dari `rmh.py`.

### Kenapa per blok lebih cepat

Waktu proses enumerative coding sebanding dengan **n²** karena rank adalah satu bilangan raksasa sebesar seluruh file. Jika file dibagi menjadi blok berukuran B:

```
tanpa blok : n²
per blok   : (n / B) blok × B²  =  n × B   → linear terhadap ukuran file
```

Blok juga **tidak saling bergantung**, jadi bisa diproses paralel di beberapa core CPU (opsi `-j`, default = jumlah core).

### Cara pakai

```bash
python byteentropy/rmh_blok.py encode   <file>     [-o <file.rmb>] [-b <ukuran_blok>] [-j <proses>]
python byteentropy/rmh_blok.py decode   <file.rmb> [-o <file_hasil>] [-j <proses>]
python byteentropy/rmh_blok.py info     <file.rmb> [--semua]
python byteentropy/rmh_blok.py analisis <file>     [-u <ukuran1> <ukuran2> ...] [-j <proses>]
```

| Perintah | Keterangan |
|---|---|
| `encode` | File asli → `.rmb`. Opsi `-b` ukuran blok (default 4096), `-j` jumlah proses paralel |
| `decode` | `.rmb` → file asli, diverifikasi dengan CRC32. Default output `<file tanpa .rmb>.decoded` |
| `info` | Rincian per blok: panjang, jumlah byte unik, ukuran rank, entropy. Opsi `--semua` menampilkan semua blok |
| `analisis` | Mencoba beberapa ukuran blok (default 256, 1024, 4096, 16384) tanpa menulis file, untuk memilih ukuran blok terbaik |

Contoh:

```bash
python byteentropy/rmh_blok.py encode "Testing/GPU List.txt" -o gpu.rmb
python byteentropy/rmh_blok.py info gpu.rmb
python byteentropy/rmh_blok.py decode gpu.rmb -o gpu_kembali.txt
python byteentropy/rmh_blok.py analisis "Testing/GPU List.txt" -u 256 1024 4096 16384 65536
```

### Struktur file

| Bagian | Ukuran | Isi |
|---|---|---|
| Magic | 4 byte | `RMB1` |
| n | varint | Ukuran file asli |
| B | varint | Ukuran blok (blok terakhir boleh lebih pendek) |
| CRC32 | 4 byte | Checksum seluruh file asli |
| **Untuk setiap blok:** | | Jumlah blok = ⌈n / B⌉, tidak disimpan |
| k | varint | Jumlah nilai byte berbeda di blok ini |
| Histogram | k × (1 byte + varint) | Pasangan (nilai byte, frekuensi) |
| Rank | m byte | Rank blok, big-endian. Panjang `m` dihitung dari histogram blok |

### Hasil: kecepatan

`Testing/GPU List.txt` (136.412 byte), CPU 16 core:

| Metode | Waktu encode | Ukuran |
|---|---|---|
| `rmh.py` (tanpa blok) | 21,6 detik | 88.067 byte |
| `rmh_blok.py -b 4096 -j 1` | 0,81 detik | 89.892 byte |
| `rmh_blok.py -b 4096 -j 16` | 0,23 detik | 89.892 byte |

Dengan blok 4.096 byte, file **27× lebih cepat** pada 1 core dan **94× lebih cepat** pada 16 core. Ukurannya hanya 2% lebih besar. Decode file yang sama butuh 0,32 detik, dan hasilnya identik.

### Hasil: memilih ukuran blok

Output `analisis` untuk `Testing/GPU List.txt`:

| Blok | Jumlah blok | Histogram | Rank | Total `.rmb` | % asli | Detik (16 proses) |
|---|---|---|---|---|---|---|
| 256 | 533 | 47.917 | 79.081 | 127.011 | 93,1% | 0,17 |
| 1.024 | 134 | 13.000 | 83.863 | 96.876 | 71,0% | 0,18 |
| 4.096 | 34 | 3.966 | 85.913 | 89.892 | 65,9% | 0,23 |
| 16.384 | 9 | 1.362 | 86.908 | 88.284 | 64,7% | 0,49 |
| 65.536 | 3 | 509 | 87.422 | 87.945 | 64,5% | 5,20 |

Ada tarik-ulur:

- **Blok kecil → bagian rank lebih kecil.** Histogram tiap blok mengikuti isi lokal blok itu, jadi lebih akurat daripada satu histogram untuk seluruh file.
- **Blok kecil → biaya histogram jauh lebih besar.** Setiap blok menyimpan histogramnya sendiri. Pada blok 256 byte, histogram memakan 47.917 byte, lebih dari sepertiga file.
- **Blok besar → lambat.** Waktu per blok naik kuadratik terhadap ukuran blok.

Untuk file ini, **4.096 – 16.384 byte** adalah titik tengah yang baik. Ukuran terbaik berbeda per file, jadi gunakan `analisis` untuk mencobanya. Contohnya, `Testing/HoRM.txt` (4.690 byte) paling kecil pada blok 1.024 byte (2.146 byte).

### Pengujian

- Encode → decode identik (dicek dengan `cmp`) untuk `Testing/GPU List.txt`, `Testing/bismillah.txt`, `Testing/nullbyte.txt`, dan `Testing/123.txt.png`.
- 300 data acak dengan ukuran 0–5.000 byte dan ukuran blok 1–4.096 byte lolos semua, termasuk mode paralel.
- File `.rmb` yang rusak ditolak:

| Kerusakan | Pesan |
|---|---|
| Bukan file `.rmb` | `Bukan file .rmb (magic tidak cocok)` |
| File terpotong | `File .rmb terpotong (rank blok N)` |
| Ada byte tambahan di akhir | `Ada N byte sisa di akhir file .rmb` |
| Rank atau histogram berubah | `CRC32 tidak cocok, hasil decode rusak` |

### Batasan

- Per blok menyelesaikan masalah **kecepatan**, bukan **ukuran**. Hasilnya tetap mendekati batas Shannon orde-0, dan masih jauh di atas zlib/lzma untuk teks (`GPU List.txt`: `.rmb` 89.892 byte, lzma 9.024 byte).
- Biaya histogram per blok besar, terutama untuk blok kecil. Ini diatasi oleh [Histogram Adaptif](#histogram-adaptif-file-rma).

## Histogram Adaptif (File .rma)

Script: `byteentropy/rmh_adaptif.py`. Ini langkah 1 dari pemodelan adaptif: **histogram tidak disimpan di file sama sekali**. `rmh.py` dan `rmh_blok.py` tidak diubah.

### Ide

Di `.rmb`, setiap blok harus menyimpan histogramnya agar decoder tahu frekuensi tiap byte. Di `.rma`, histogram **dipelajari dari byte-byte yang sudah terbuka**:

1. Awalnya semua 256 nilai byte punya frekuensi 1, jadi tidak ada byte yang mustahil.
2. Byte berikutnya dikodekan sesuai peluangnya menurut histogram saat itu.
3. Setelah byte terbuka, frekuensinya ditambah (default +32).
4. Jika total frekuensi melewati batas (default 65.536), semua frekuensi dibagi dua. Data lama perlahan dilupakan, sehingga data terbaru lebih dipercaya.

Encoder dan decoder menjalankan langkah yang **persis sama** dengan data yang sama, sehingga histogram tebakan mereka selalu identik. Inilah bentuk nyata dari ide "bagian yang sudah terbuka memberi informasi bagian berikutnya": informasinya tidak perlu disimpan, karena decoder bisa menyimpulkannya sendiri.

### Rank tetap ada: arithmetic coding

Rank di `.rmh` adalah nomor urut di antara semua susunan. Di `.rma`, rank dihitung **bertahap per byte** dengan *arithmetic coding*:

- Mulai dari interval `[0, 1)`.
- Setiap byte mempersempit interval sebesar peluangnya. Byte yang sering muncul hanya sedikit mempersempit, sehingga butuh sedikit bit.
- Bilangan di dalam interval akhir itulah "rank" seluruh file.

Program memakai coder integer 32-bit (Witten, Neal & Cleary, 1987), jadi waktunya **linear** tanpa bilangan raksasa. Histogram disimpan dalam Fenwick tree, sehingga frekuensi kumulatif dihitung dalam 8 langkah, bukan 256.

### Hubungan dengan enumerative coding

Jika model adaptif memakai penambahan +1 tanpa pembagian dua, jumlah bit yang dihasilkan **persis sama** dengan:

```
log2(jumlah histogram yang mungkin) + log2(jumlah susunan)
= log2 C(n+255, 255)               + log2(n! / (c1!·...·ck!))
= nomor histogram                   + rank
```

Diverifikasi pada `Testing/HoRM.txt`: keduanya menghasilkan **18.596,771 bit** (1.443,687 + 17.153,085). Jadi model adaptif adalah enumerative coding (histogram + rank) yang histogramnya ikut dikodekan secara implisit. Varian default (+32 dengan pembagian dua) sedikit lebih baik, karena mengikuti perubahan isi lokal file seperti blok kecil di `.rmb`, tapi tanpa biaya histogram.

### Cara pakai

```bash
python byteentropy/rmh_adaptif.py encode     <file>     [-o <file.rma>] [--tambah N] [--batas N]
python byteentropy/rmh_adaptif.py decode     <file.rma> [-o <file_hasil>]
python byteentropy/rmh_adaptif.py bandingkan <file>     [-b <blok .rmb>] [--tambah N] [--batas N]
```

| Perintah / opsi | Keterangan |
|---|---|
| `encode` | File asli → `.rma` |
| `decode` | `.rma` → file asli, diverifikasi dengan CRC32. Parameter model dibaca dari header |
| `bandingkan` | Membandingkan `.rmb`, `.rma`, zlib, dan lzma tanpa menulis file |
| `--tambah` | Penambahan frekuensi tiap byte muncul (1..65.536, default 32). Makin besar, makin cepat beradaptasi |
| `--batas` | Total frekuensi maksimum sebelum dibagi dua (512..16.777.216, default 65.536). Makin kecil, makin cepat melupakan data lama |

Contoh:

```bash
python byteentropy/rmh_adaptif.py encode "Testing/GPU List.txt" -o gpu.rma
python byteentropy/rmh_adaptif.py decode gpu.rma -o gpu_kembali.txt
python byteentropy/rmh_adaptif.py bandingkan "Testing/GPU List.txt"
```

Output `bandingkan`:

```
Metode                        Histogram    Rank/kode        Total    % asli
.rmb (blok 4096)                   3966        85913        89892     65.9%
.rma (adaptif)                        0        87372        87387     64.1%
zlib -9                                                     11285      8.3%
lzma -9                                                      9024      6.6%
```

### Struktur file

| Bagian | Ukuran | Isi |
|---|---|---|
| Magic | 4 byte | `RMA1` |
| n | varint | Ukuran file asli |
| tambah | varint | Parameter model |
| batas | varint | Parameter model |
| CRC32 | 4 byte | Checksum file asli |
| Kode | sisa file | Hasil arithmetic coding (rank) |

**Tidak ada histogram.** Header hanya sekitar 14 byte, berapa pun ukuran file-nya.

### Hasil

| File | Asli | `.rmb` (blok 4096) | `.rma` | lzma |
|---|---|---|---|---|
| `Testing/bismillah.txt` | 9 | 29 | 22 | 68 |
| `Testing/nullbyte.txt` | 256 | 16 | 22 | 72 |
| `Testing/HoRM.txt` | 4.690 | 2.224 | 2.119 | 1.024 |
| `Testing/RMHash_HoRM2.txt` | 8.585 | 3.872 | 3.878 | 584 |
| `Testing/Return[er]Machine-NestedRubik256DNA.py` | 15.112 | 15.745 | 14.484 | 12.208 |
| `Testing/123.txt.png` | 10.073 | 11.030 | 10.086 | 8.264 |
| `Testing/GPU List.txt` | 136.412 | 89.892 | 87.387 | 9.024 |

(ukuran dalam byte)

- `.rma` lebih kecil dari `.rmb` pada hampir semua file, terutama file dengan banyak nilai byte berbeda (PNG, kode Python), di mana histogram per blok mahal.
- `.rma` tidak pernah membesar jauh dari ukuran asli. PNG yang sudah terkompresi hanya bertambah 13 byte (header + CRC32).
- `nullbyte.txt` sedikit lebih besar dari `.rmb` karena model butuh beberapa byte untuk "belajar" bahwa hanya byte 0 yang muncul.

### Kecepatan

| File | Encode | Decode |
|---|---|---|
| `HoRM.txt` (4,7 KB) | 0,02 detik | 0,02 detik |
| `GPU List.txt` (136 KB) | 0,53 detik | 0,68 detik |

Waktunya linear dan cukup dengan 1 core. Tidak perlu dipecah per blok, jadi model bisa terus belajar dari awal sampai akhir file.

### Pengujian

- Encode → decode identik (dicek dengan `cmp`) untuk ketujuh file di tabel hasil.
- 412 uji acak lolos, termasuk file kosong, 100.000 byte nol, data acak penuh, dan kombinasi parameter ekstrem (`--tambah 1 --batas 512` sampai `--tambah 65536 --batas 16777216`).
- File rusak ditolak: magic salah (`Bukan file .rma`), header terpotong (`File .rma terpotong`), serta kode yang terpotong atau diubah (`CRC32 tidak cocok`).

### Batasan

- Masih **orde-0**: setiap byte ditebak hanya dari frekuensi keseluruhan, tanpa melihat byte di sebelahnya. Karena itu ukurannya tetap mendekati batas Shannon orde-0 dan masih jauh di atas lzma untuk teks.
- Langkah 2 menebak setiap byte dari byte-byte sebelumnya, lihat [Konteks PPM](#konteks-ppm-file-rmk).

## Konteks PPM (File .rmk)

Script: `byteentropy/rmh_konteks.py`. Ini langkah 2 dari pemodelan adaptif: **satu histogram adaptif per konteks**. File-file sebelumnya tidak diubah.

### Ide

`.rma` hanya punya satu histogram untuk seluruh file. Padahal peluang sebuah byte sangat bergantung pada byte sebelumnya. Di teks, setelah `ban` kemungkinan besar muncul `k`, dan setelah `q` hampir pasti `u`.

`.rmk` menyimpan histogram terpisah untuk setiap **konteks** (1..N byte sebelumnya), dan semuanya dipelajari sambil jalan seperti di `.rma`. Histogram tetap **tidak disimpan di file**.

### Masalah konteks panjang dan solusinya (PPM)

Konteks panjang lebih tajam tebakannya, tapi sering **belum pernah dilihat**. Kalau setiap konteks baru dimulai dari 256 frekuensi, biaya belajarnya menghabiskan keuntungannya. Solusinya adalah *Prediction by Partial Matching* (PPM):

1. Coba konteks terpanjang (orde N, misalnya 3 byte sebelumnya).
2. Jika byte belum pernah muncul di konteks itu, kodekan tanda **ESCAPE**, lalu turun ke konteks yang lebih pendek (orde N−1, ..., 0).
3. Orde −1: semua 256 nilai byte berpeluang sama, jadi pasti berhasil.
4. Byte yang sudah gagal di konteks panjang **dikecualikan** di konteks berikutnya (*exclusion*), supaya peluangnya tidak terbuang.

Contoh dengan orde 3, saat menebak byte setelah `...ban`:

```
konteks "ban" → pernah melihat {k, y}     → byte "k" ada      → kodekan "k"    (murah)
konteks "ban" → pernah melihat {k, y}     → byte "g" tidak ada → ESCAPE
konteks "an"  → pernah melihat {k, y, d, g} tanpa k,y → "g" ada → kodekan "g"
```

Peluang di satu konteks memakai metode escape PPM-D:

| Kejadian | Bobot |
|---|---|
| Byte `x` | `2 × frekuensi(x) − 1` |
| ESCAPE | jumlah byte berbeda di konteks itu |

### Cara pakai

```bash
python byteentropy/rmh_konteks.py encode     <file>     [-o <file.rmk>] [-k <orde>]
python byteentropy/rmh_konteks.py decode     <file.rmk> [-o <file_hasil>]
python byteentropy/rmh_konteks.py bandingkan <file>     [-k <orde1> <orde2> ...]
```

| Perintah / opsi | Keterangan |
|---|---|
| `encode` | File asli → `.rmk`, sekaligus menampilkan berapa byte yang berhasil ditebak di tiap orde |
| `decode` | `.rmk` → file asli, diverifikasi dengan CRC32. Orde dibaca dari header |
| `bandingkan` | Membandingkan `.rmb`, `.rma`, `.rmk` di beberapa orde, zlib, dan lzma, tanpa menulis file |
| `-k`, `--orde` | Panjang konteks maksimum 0..6 (default 3) |

Contoh:

```bash
python byteentropy/rmh_konteks.py encode "Testing/GPU List.txt" -o gpu.rmk
python byteentropy/rmh_konteks.py decode gpu.rmk -o gpu_kembali.txt
python byteentropy/rmh_konteks.py bandingkan "Testing/GPU List.txt" -k 1 2 3 4 5 6
```

Output `encode`:

```
Rincian file .rmk:
  header                8 byte
  crc32                 4 byte
  histogram             0 byte
  kode (rank)       12519 byte
  TOTAL             12531 byte

Ukuran  : 136412 -> 12531 byte (9.2% dari asli)

Byte berhasil ditebak di konteks orde:
  orde  3 :   130468 byte ( 95.6%)  dari 2740 konteks
  orde  2 :     3201 byte (  2.3%)  dari 756 konteks
  orde  1 :     1986 byte (  1.5%)  dari 75 konteks
  orde  0 :      682 byte (  0.5%)  dari 1 konteks
  orde -1 :       75 byte (  0.1%)  byte yang benar-benar baru
```

95,6% byte berhasil ditebak dari 3 byte sebelumnya. Hanya 75 byte yang benar-benar baru, yaitu kemunculan pertama setiap nilai byte yang dipakai file ini.

### Struktur file

| Bagian | Ukuran | Isi |
|---|---|---|
| Magic | 4 byte | `RMK1` |
| n | varint | Ukuran file asli |
| Orde | 1 byte | Panjang konteks maksimum |
| CRC32 | 4 byte | Checksum file asli |
| Kode | sisa file | Hasil arithmetic coding |

### Hasil

Ukuran dalam byte. **Tebal** = paling kecil di antara metode Return[er] Machine.

| File | Asli | `.rma` | `.rmk` orde 1 | orde 2 | orde 3 | orde 4 | orde 5 | zlib -9 | lzma -9 |
|---|---|---|---|---|---|---|---|---|---|
| `GPU List.txt` | 136.412 | 87.387 | 36.578 | 16.019 | 12.531 | 11.143 | **11.006** | 11.285 | 9.024 |
| `HoRM.txt` | 4.690 | 2.119 | 1.402 | 1.185 | **1.085** | 1.114 | 1.137 | 1.236 | 1.024 |
| `RMHash_HoRM2.txt` | 8.585 | 3.878 | 1.684 | 1.174 | **975** | 1.021 | 1.079 | 1.146 | 584 |
| `Return[er]Machine.py` | 7.235 | 4.482 | 3.120 | 2.346 | 2.204 | 2.175 | **2.174** | 2.103 | 2.168 |
| `NestedRubik256DNA.py` | 15.112 | 14.484 | 14.277 | 13.825 | 13.741 | **13.739** | 13.749 | 12.354 | 12.208 |
| `123.txt.png` | 10.073 | 10.086 | 9.029 | 8.697 | 8.679 | **8.672** | 8.673 | 8.369 | 8.264 |

- **Lompatan besar dari `.rma`**: `GPU List.txt` turun dari 87.387 menjadi 11.006 byte (8× lebih kecil).
- `.rmk` **mengalahkan zlib** pada `GPU List.txt`, `HoRM.txt`, dan `RMHash_HoRM2.txt`. Pada `Return[er]Machine.py` hasilnya hampir setara lzma (2.174 vs 2.168) dan sedikit di atas zlib (2.103).
- **Orde terbaik berbeda per file.** File kecil cocok dengan orde 3, karena konteks panjang belum sempat dipelajari. File besar cocok dengan orde 4–5. Orde 6 mulai memburuk karena terlalu banyak konteks yang jarang terlihat. Gunakan `bandingkan` untuk mencari orde terbaik.
- lzma masih unggul pada file yang **sangat berulang** (`RMHash_HoRM2.txt`: 584 vs 975), karena lzma bisa menyalin potongan panjang sekaligus, sedangkan PPM tetap menebak satu byte demi satu byte.
- File yang sudah terkompresi (PNG) dan kode biner-acak (`NestedRubik256DNA.py`) hanya sedikit mengecil, karena isinya memang hampir tidak berpola.

### Kecepatan

| File | Orde | Encode | Decode |
|---|---|---|---|
| `GPU List.txt` (136 KB) | 3 | 0,8–1,5 detik | 1,4 detik |
| `NestedRubik256DNA.py` (15 KB) | 3 | 0,6 detik | - |

Waktunya tetap linear. File dengan banyak byte baru (biner) lebih lambat, karena escape ke orde −1 harus menelusuri daftar 256 nilai byte.

### Pengujian

- Encode → decode identik (dicek dengan `cmp`) untuk kedelapan file uji (`GPU List.txt`, `HoRM.txt`, `RMHash_HoRM2.txt`, `Return[er]Machine.py`, `NestedRubik256DNA.py`, `123.txt.png`, `bismillah.txt`, `nullbyte.txt`) pada orde 3 dan 5.
- 412 uji acak lolos untuk semua orde 0..6, termasuk file kosong, 50.000 byte nol, data acak penuh, dan pola `abab...`.
- File rusak ditolak: magic salah, header terpotong, orde tidak valid, dan kode yang diubah (`CRC32 tidak cocok`).
- Catatan: memotong 1–3 byte terakhir kadang **tetap menghasilkan file yang benar** (CRC32 cocok). Byte terakhir arithmetic coder hanya bantalan presisi, dan decoder mengisi bit yang hilang dengan nol. Pemotongan yang lebih banyak terdeteksi oleh CRC32.

### Batasan dan arah berikutnya

- Python murni: sekitar 100 KB/detik. Untuk file besar (MB), implementasi perlu dipindah ke bahasa yang lebih cepat (C/Rust) atau dipercepat dengan numba.
- lzma masih unggul untuk data yang sangat berulang. Arah pengembangan: **pencampuran konteks** (*context mixing*, seperti PAQ/cmix), yaitu menggabungkan tebakan dari beberapa orde sekaligus alih-alih memilih satu lewat escape, atau menambahkan model "salin potongan" seperti LZ.

## Melihat Isi File .rmk

Script: `byteentropy/rmh_konteks_info.py`. Fungsinya seperti `rmh_blok.py info`, tapi untuk file `.rmk`. `rmh_konteks.py` tidak diubah.

### Kenapa harus memutar ulang decode

Di `.rmb`, setiap blok **menyimpan** histogram + rank, jadi `info` cukup membaca file. Di `.rmk`, file hanya berisi header, CRC32, dan bit arithmetic coding. **Histogram dan konteks tidak disimpan sama sekali.** Karena itu `rmh_konteks_info.py` mendekode ulang seluruh file sambil mencatat setiap langkah:

- konteks orde berapa yang berhasil menebak setiap byte,
- berapa kali ESCAPE terjadi,
- berapa bit yang dihabiskan setiap kejadian: `bit = log2(total / lebar interval)`.

Di akhir, hasil decode dicocokkan dengan CRC32, sehingga angka yang ditampilkan dijamin berasal dari decode yang benar.

### Cara pakai

```bash
python byteentropy/rmh_konteks_info.py <file.rmk> [-s <ukuran_segmen>] [--semua] [-t <jumlah_konteks>] [--jejak N] [--dari POSISI]
```

| Opsi | Keterangan |
|---|---|
| `-s`, `--segmen` | Ukuran segmen untuk tabel rincian (default 4096, sama dengan blok `.rmb` supaya bisa dibandingkan) |
| `--semua` | Tampilkan semua segmen. Tanpa opsi ini, hanya 10 segmen pertama dan 5 terakhir |
| `-t`, `--konteks` | Jumlah konteks teratas yang ditampilkan (default 10, `0` = tidak ditampilkan) |
| `--jejak N` | Tampilkan langkah decode untuk N byte |
| `--dari POSISI` | Posisi awal jejak (default 0) |

Contoh:

```bash
python byteentropy/rmh_konteks.py encode "Testing/GPU List.txt" -o gpu.rmk
python byteentropy/rmh_konteks_info.py gpu.rmk
python byteentropy/rmh_konteks_info.py gpu.rmk --jejak 12 --dari 100000
```

### Membaca output

Output untuk `gpu.rmk` (orde 3) terdiri dari lima bagian.

**1. Isi file (yang benar-benar tersimpan)**

```
  Offset  Ukuran  Bagian  Isi
       0       4  magic   52 4D 4B 31              ("RMK1")
       4       3  n       DC A9 08                 (136412)
       7       1  orde    03                       (3)
       8       4  crc32   2B 7D EF A4
      12   12519  kode    68 B9 F5 7A DE 8C ...    (bit arithmetic coding)
  Histogram / konteks : 0 byte (tidak disimpan, dibangun ulang saat decode)
```

Hanya 12 byte header. Sisanya adalah satu deretan bit (kode) untuk seluruh file.

**2. Rincian per segmen**

```
  Segmen  Panjang   Offset  Kode (byte)  bit/byte   Orde 3   Escape   Baru
       0     4096       12        614.8     1.201    86.1%      472     58
       1     4096      626        358.1     0.699    94.3%      206      1
       2     4096      984        313.7     0.613    95.0%      177      2
       3     4096     1298        292.3     0.571    96.2%      136      1
     ...
      33     1244    12335        195.2     1.255    91.8%       94      0
```

| Kolom | Arti |
|---|---|
| Offset | Posisi (byte) di file `.rmk` tempat kode segmen ini dimulai. Arithmetic coding menulis bit berurutan, jadi segmen 0 ada di awal kode |
| Kode (byte) | Berapa byte kode yang dihabiskan segmen ini |
| bit/byte | Rata-rata bit per byte asli. 8 = tidak terkompresi |
| Orde 3 | Persentase byte yang berhasil ditebak di konteks terpanjang |
| Escape | Berapa kali turun ke konteks lebih pendek |
| Baru | Berapa nilai byte yang muncul untuk pertama kali |

Segmen 0 paling mahal (614,8 byte) karena model masih belajar: 58 nilai byte baru muncul di sana. Mulai segmen 1, biayanya turun menjadi sekitar 300–400 byte. Bandingkan dengan `.rmb` untuk file yang sama: **setiap** blok 4.096 byte butuh sekitar 2.500 byte rank ditambah histogramnya sendiri, karena setiap blok mulai dari nol.

**3. Ke mana bit kode dihabiskan**

```
  Kejadian                  Jumlah  Kode (byte)  Rata-rata bit
  byte di orde 3            130468       8046.3          0.493
  byte di orde 2              3201       1099.4          2.748
  byte di orde 1              1986        965.7          3.890
  byte di orde 0               682        536.7          6.296
  byte baru (orde -1)           75         72.8          7.768
  ESCAPE                      5364       1797.2          2.680
  TOTAL (per byte asli)     136412      12518.2          0.734
  Kode sebenarnya: 12519 byte (selisih = presisi arithmetic coder + bantalan akhir)
```

- Byte yang tertebak di orde 3 hanya butuh rata-rata **0,49 bit**, jauh di bawah 8 bit.
- Makin pendek konteksnya, makin mahal biayanya. Byte yang benar-benar baru butuh sekitar 7,8 bit.
- ESCAPE memakan 1.797 byte (14% kode). Ini harga yang dibayar setiap kali konteks panjang gagal menebak.
- Total hitungan (12.518,2 byte) cocok dengan ukuran kode sebenarnya (12.519 byte).

**4. Konteks yang dipelajari**

```
  orde 3 :   2740 konteks
  ...
10 konteks orde 3 yang paling sering menebak dengan benar:
  Konteks    Benar  Byte berikutnya (frekuensi saat ini)
  "ion"       2880  ' ':962 '_':959 '\r':959 'i':4
  "tio"       2877  'n':2878
  "opt"       2876  'i':2877
  "pti"       2876  'o':2877
```

Inilah "histogram per konteks" yang tidak pernah disimpan di file. Contohnya, setelah `tio` byte berikutnya **selalu** `n` (2.878 kali), jadi byte itu hampir tidak butuh bit. Kata `option` di HTML file ini sangat sering muncul. Frekuensi bisa jauh lebih kecil dari jumlah "Benar" karena frekuensi di satu konteks dibagi dua saat salah satunya melewati 4.096 atau totalnya melewati 8.192.

**5. Jejak decode (opsional, `--jejak`)**

Awal file `Testing/bismillah.txt` (`--jejak 9`), ketika model belum tahu apa-apa. Ini cuplikan, sebagian baris dihilangkan:

```
   Posisi Byte   Konteks     Bit  Langkah
        0 'b'    ""         8.00  o0:-  o-1:BARU 8.00
        1 'i'    "b"        8.99  o1:-  o0:ESC 1.00  o-1:BARU 7.99
      ...
        4 'i'    "ism"      3.00  o3:-  o2:-  o1:-  o0:OK 3.00
        5 'l'    "smi"     10.39  o3:-  o2:-  o1:ESC 1.00  o0:ESC 1.42  o-1:BARU 7.98
```

Tengah file `GPU List.txt` (`--jejak 12 --dari 100000`), ketika model sudah banyak belajar. Ini juga cuplikan:

```
   Posisi Byte   Konteks     Bit  Langkah
   100000 '6'    "=\"1"     6.42  o3:OK 6.42
   100001 '4'    "\"16"     9.11  o3:ESC 2.00  o2:ESC 5.92  o1:OK 1.20
   100002 '3'    "164"      5.05  o3:-  o2:OK 5.05
   100003 '"'    "643"      1.00  o3:OK 1.00
   100004 ' '    "43\""     0.05  o3:OK 0.05
      ...
   100006 'l'    "\" c"     0.00  o3:OK 0.00
   100007 'a'    " cl"      0.00  o3:OK 0.00
```

| Simbol | Arti |
|---|---|
| `o3`, `o2`, ... | Konteks orde 3, 2, ... |
| `-` | Konteks itu belum pernah terlihat, jadi dilewati tanpa biaya |
| `OK 0.05` | Byte berhasil ditebak di konteks itu, biayanya 0,05 bit |
| `ESC 2.00` | Byte belum pernah muncul di konteks itu. Kirim ESCAPE (2 bit), lalu turun |
| `BARU 7.98` | Byte belum pernah muncul di file sama sekali (orde −1) |

Angka ID seperti `164` sulit ditebak (5–9 bit per byte), sedangkan teks ` class="` yang sudah ribuan kali muncul hampir gratis. `0.00` berarti kurang dari 0,005 bit.

### Contoh file besar: `Testing/logfactorial.txt`

| | Ukuran |
|---|---|
| Asli | 5.644.322 byte |
| zlib -9 | 2.413.002 byte |
| lzma -9 | 2.270.136 byte |
| **`.rmk` orde 3** | **2.130.339 byte** |

Pada file ini `.rmk` **lebih kecil dari lzma -9**. Hasil `info` menjelaskan alasannya:

```
5 konteks orde 3 yang paling sering menebak dengan benar:
  Konteks    Benar  Byte berikutnya (frekuensi saat ini)
  "000"     520914  '0':2333 '\r':6 '7':3 '1':3 '4':3 '8':3 ... (+6)
  "400"       5572  '0':1022 '9':539 '1':527 '3':513 '4':508 '2':506 ... (+5)
```

- File ini berisi angka besar dengan banyak deretan nol. Setelah `000`, byte berikutnya hampir pasti `0` lagi, jadi deretan nol hampir gratis.
- Setelah digit lain (`400`, `600`, ...), digit berikutnya tersebar hampir merata. Digit seperti ini memang tidak bisa diperkecil di bawah sekitar log2(10) ≈ 3,32 bit.
- Rata-rata keseluruhan **3,02 bit per byte**. lzma kurang efektif di sini karena angka-angka itu jarang berulang sebagai potongan panjang, sedangkan PPM unggul dalam memprediksi pola pendek seperti deretan nol.

Memutar ulang decode file 5,6 MB ini butuh sekitar 43 detik (sekitar 130 KB/detik).

### Pengujian

- Diuji pada `.rmk` dari `GPU List.txt` (orde 3), `bismillah.txt`, `nullbyte.txt` (orde 0), `123.txt.png` (orde 6, segmen 2.048), file kosong, dan `logfactorial.txt` (5,6 MB). Pada semua file CRC32 cocok, dan total biaya yang dihitung ulang berselisih paling banyak 1 byte dari ukuran kode sebenarnya.
- File rusak atau bukan `.rmk` ditolak (`CRC32 tidak cocok`, `Bukan file .rmk`). Opsi tidak valid (`-s 0`, nilai negatif) ditolak dengan pesan yang jelas.

## Return[er] Machine Final (File .rmf)

Script: `byteentropy/rmh_final.py`. **Ini versi yang disarankan untuk dipakai.** Script ini menggabungkan hasil terbaik dari semua tahap sebelumnya. File-file sebelumnya tidak diubah.

### Tujuan

Returner Machine adalah gabungan kompresi dan generator file. `.rmf` memenuhi empat sifat berikut:

| Sifat | Cara mencapainya |
|---|---|
| Hasil sekecil mungkin | Mode terbaik dipilih otomatis: konteks orde 1..5, adaptif, atau mentah |
| Bisa digenerate kembali ke file asli | Semua mode lossless, dan setiap decode diverifikasi |
| Konsisten seperti hash | Deterministik: file yang sama selalu menghasilkan `.rmf` yang sama persis |
| Sidik jari berukuran tetap | SHA-256 file asli (32 byte) disimpan di header |

Yang **tidak mungkin** adalah ukuran hasil yang selalu tetap untuk semua file. Hash berukuran tetap tidak bisa dibalik menjadi file asli (prinsip sarang merpati). Karena itu `.rmf` memisahkan dua peran: SHA-256 sebagai **identitas** berukuran tetap, dan kode sebagai **resep** untuk membangun kembali file-nya, yang ukurannya mengikuti jumlah informasi di dalam file.

### Cara memilih mode

1. Semua kandidat diuji: **mentah**, **adaptif** (`.rma`), dan **konteks orde 1–5** (`.rmk`).
2. Yang menghasilkan kode terkecil dipilih. Jika ada yang sama besar, kandidat yang lebih sederhana dipilih, sehingga pilihannya juga deterministik.
3. Untuk file di atas 256 KB, pengujian memakai **sampel** 3 × 64 KB (awal, tengah, dan akhir file) supaya tidak perlu mengodekan file besar 7 kali. Sampel cenderung memilih orde terlalu rendah, karena konteks panjang belum sempat dipelajari. Karena itu, file penuh dikodekan dengan orde terpilih, lalu dicoba orde berikutnya (+1, +2, ...) selama hasilnya masih mengecil.
4. Jika hasil akhirnya tidak lebih kecil dari file asli, file disimpan **mentah**. Data acak atau yang sudah terkompresi tidak pernah membengkak, hanya bertambah sebesar header.
5. Secara default, hasil encode langsung **didekode ulang dan dicocokkan** sebelum file ditulis.

### Cara pakai

```bash
python byteentropy/rmh_final.py encode <file>     [-o <file.rmf>] [-k <orde>] [--tanpa-verifikasi]
python byteentropy/rmh_final.py decode <file.rmf> [-o <file_hasil>]
python byteentropy/rmh_final.py info   <file.rmf>
```

| Perintah / opsi | Keterangan |
|---|---|
| `encode` | File asli → `.rmf`. Menampilkan hasil uji setiap kandidat dan mode yang terpilih |
| `decode` | `.rmf` → file asli. Hasilnya diverifikasi dengan SHA-256 |
| `info` | Menampilkan mode, ukuran asli, dan SHA-256 dari header tanpa decode (instan) |
| `-k`, `--orde` | Paksa mode konteks dengan orde tertentu (0..6), tanpa pemilihan otomatis |
| `--tanpa-verifikasi` | Lewati decode ulang setelah encode. Lebih cepat, tapi tanpa jaminan tambahan |

Contoh:

```bash
python byteentropy/rmh_final.py encode "Testing/GPU List.txt" -o gpu.rmf
python byteentropy/rmh_final.py info gpu.rmf
python byteentropy/rmh_final.py decode gpu.rmf -o gpu_kembali.txt
```

Output `encode`:

```
Uji kandidat (file penuh):
  Kandidat            Kode (byte)     % uji     Detik
  mentah                   136412    100.0%     0.000
  adaptif                   87372     64.1%     0.342
  konteks orde 1            36566     26.8%     0.587
  konteks orde 2            16007     11.7%     0.475
  konteks orde 3            12519      9.2%     0.512
  konteks orde 4            11131      8.2%     0.620
  konteks orde 5            10994      8.1%     0.740  <- terpilih

Mode       : konteks orde 5
SHA-256    : 2d8543fd1ab9c08c45c8f4c73345d129a49585e105a1f77121e9e24869aeb4a4
Ukuran     : 136412 -> 11035 byte (8.1% dari asli)
Verifikasi : decode identik, SHA-256 cocok (0.772 detik)
```

SHA-256 di atas sama dengan hasil `sha256sum "Testing/GPU List.txt"`, jadi sidik jari file bisa dicek tanpa decode lewat perintah `info`.

### Struktur file

| Bagian | Ukuran | Isi |
|---|---|---|
| Magic | 4 byte | `RMF1` |
| Mode | 1 byte | `0` = mentah, `1` = adaptif, `2` = konteks |
| n | varint | Ukuran file asli |
| SHA-256 | 32 byte | Sidik jari file asli |
| Parameter | 0–4 byte | Mode adaptif: `tambah`, `batas` (varint). Mode konteks: orde (1 byte) |
| Kode / data | sisa file | Data mentah atau bit arithmetic coding |

Header berukuran 38–45 byte, terutama untuk SHA-256.

### Hasil

| File | Asli | Mode terpilih | `.rmf` | `.rmk` orde 3 | lzma -9 |
|---|---|---|---|---|---|
| `GPU List.txt` | 136.412 | konteks orde 5 | **11.035** | 12.531 | 9.024 |
| `logfactorial.txt` | 5.644.322 | konteks orde 3 | **2.130.368** | 2.130.339 | 2.270.136 |
| `HoRM.txt` | 4.690 | konteks orde 3 | 1.114 | 1.085 | 1.024 |
| `RMHash_HoRM2.txt` | 8.585 | konteks orde 3 | 1.004 | 975 | 584 |
| `Return[er]Machine.py` | 7.235 | konteks orde 5 | 2.203 | 2.204 | 2.168 |
| `NestedRubik256DNA.py` | 15.112 | konteks orde 4 | 13.768 | 13.741 | 12.208 |
| `123.txt.png` | 10.073 | konteks orde 4 | 8.701 | 8.679 | 8.264 |
| `nullbyte.txt` | 256 | konteks orde 1 | 42 | 14 | 72 |
| 100.000 byte acak | 100.000 | mentah | **100.040** | 110.019 | 100.064 |
| `bismillah.txt` | 9 | mentah | 47 | 20 | 68 |

(ukuran dalam byte)

- Jika orde terbaik bukan 3, `.rmf` lebih kecil dari `.rmk` orde 3 karena ordenya dipilih otomatis (`GPU List.txt`: orde 5, 11.035 vs 12.531). Jika orde terbaik memang 3 (`logfactorial.txt`), ukurannya sama ditambah selisih header.
- Untuk data acak, `.rmf` hanya bertambah 40 byte (header). `.rmk` membengkak sekitar 10%.
- Untuk file kecil, `.rmf` sekitar 29 byte lebih besar dari `.rmk`, karena SHA-256 (32 byte) menggantikan CRC32 (4 byte). Itu harga untuk sidik jari yang jauh lebih kuat.

### Pengujian

- Encode → decode identik (dicek dengan `cmp`) untuk semua file di tabel hasil, termasuk file kosong.
- Encode dua kali selalu menghasilkan file `.rmf` yang **sama persis** (deterministik).
- 157 uji acak lolos, termasuk orde paksa 0..6 dan pengecekan determinisme.
- File rusak ditolak: magic salah, mode tidak dikenal, header terpotong, data mentah terpotong, serta kode, data, atau SHA-256 yang diubah (`SHA-256 tidak cocok`).

### Batasan

- Pemilihan otomatis mengodekan file sampai 7 kali, jadi encode lebih lambat dari `rmh_konteks.py`. Decode tetap secepat mode yang terpilih.
- Contoh file besar, `Testing/logfactorial.txt` (5,6 MB): sampel memilih orde 2, lalu penyesuaian pada file penuh menemukan orde 3 lebih kecil (2.130.326 vs 2.141.867 byte kode) dan berhenti di orde 4 yang lebih besar (2.185.819). Encode butuh sekitar 103 detik ditambah verifikasi 35 detik. Decode sekitar 33 detik. Gunakan `-k 3` untuk melewati pemilihan jika orde terbaik sudah diketahui.
- Python murni sekitar 100–150 KB/detik untuk mode konteks.
- File yang sebagian besar sudah terkompresi (PDF bergambar, installer, arsip) lambat dan sedikit membengkak, karena seluruh file dipaksa melewati satu model. Ini diperbaiki di versi 2.

## Mode Campuran per Blok (.rmf versi 2)

Script: `byteentropy/rmh_final2.py`. Format tetap berekstensi `.rmf` dengan penanda **`RMF2`**. `rmh_final2.py` juga bisa membuka file `RMF1`. `rmh_final.py` tidak diubah.

### Masalah yang diperbaiki

`Testing/Dialog_Dengan_Jin_Muslim.pdf` (6.877.939 byte) hampir seluruhnya berisi data yang sudah terkompresi:

| Bagian PDF | Ukuran | lzma -9 |
|---|---|---|
| Gambar FlateDecode | 3.600.270 | 100,0% |
| Gambar JPEG (DCTDecode) | 1.564.237 | 96,7% |
| Stream FlateDecode lain | 830.822 | 100,0% |
| **Struktur PDF (teks)** | **873.765** | **7,9%** |

Di `RMF1`, seluruh 6,9 MB dipaksa melewati model konteks. Pada data yang sudah terkompresi, model ini lambat (sekitar 35 KB/detik) dan malah membengkakkan data 1–3,5%.

### Cara kerja

1. File dibagi menjadi blok 1.024 byte.
2. Setiap blok dihitung entropy orde-0-nya. Blok di atas **7,6 bit/byte** (hampir acak atau sudah terkompresi) ditandai **mentah**. Blok lainnya ditandai **model**.
3. Semua blok model **digabung menjadi satu aliran** dan dikodekan dengan mode terbaik (pemilihan dari `rmh_final.py`). Karena digabung, model tetap belajar dari seluruh bagian berpola, meskipun bagian itu tersebar di antara gambar.
4. Blok mentah disalin apa adanya, jadi tidak membengkak dan sangat cepat.
5. **Pengaman:** entropy orde-0 yang tinggi belum tentu berarti tidak bisa diperkecil. PNG, misalnya, masih bisa diperkecil oleh model konteks. Karena itu "campuran" dibandingkan dengan "semua blok dikodekan model" (konteks orde 3, pada file penuh atau sampel 3 × 64 KB), lalu yang lebih kecil dipakai.

Hasil pembagian blok disimpan sebagai **peta blok**, 1 bit per blok (`info` menampilkannya):

```
Peta blok (M = model, . = mentah, 64 blok per baris):
         0  M..MMM..MM..M..M.......M.......M............MM....MM.MMM.M.M..M.
        64  .M...M...M...M....M...M.M.M..M....M....M....M....M....M..M...M..
       ...
       448  ................................................................
```

`M` adalah struktur teks PDF yang tersebar di antara gambar (`.`).

### Cara pakai

```bash
python byteentropy/rmh_final2.py encode <file>     [-o <file.rmf>] [-b <blok>] [-a <ambang>] [-k <orde>] [--tanpa-verifikasi]
python byteentropy/rmh_final2.py decode <file.rmf> [-o <file_hasil>]
python byteentropy/rmh_final2.py info   <file.rmf> [--semua]
```

| Opsi | Keterangan |
|---|---|
| `-b`, `--blok` | Ukuran blok (default 1.024 byte) |
| `-a`, `--ambang` | Blok dengan entropy di atas ambang disimpan mentah (default 7,6). `8` = semua blok dikodekan model, sama seperti `RMF1` |
| `-k`, `--orde` | Paksa orde konteks untuk bagian berpola |
| `--tanpa-verifikasi` | Lewati decode ulang setelah encode |
| `info --semua` | Tampilkan seluruh peta blok |

Contoh:

```bash
python byteentropy/rmh_final2.py encode Testing/Dialog_Dengan_Jin_Muslim.pdf -o jin.rmf
python byteentropy/rmh_final2.py info jin.rmf
python byteentropy/rmh_final2.py decode jin.rmf -o jin_kembali.pdf
```

### Struktur file

| Bagian | Ukuran | Isi |
|---|---|---|
| Magic | 4 byte | `RMF2` |
| n | varint | Ukuran file asli |
| SHA-256 | 32 byte | Sidik jari file asli |
| B | varint | Ukuran blok |
| Peta blok | ⌈jumlah blok / 8⌉ byte | 1 bit per blok: 1 = model, 0 = mentah |
| Mode model | 1 byte | `0` mentah, `1` adaptif, `2` konteks |
| Parameter | 0–4 byte | Sama seperti `RMF1` |
| Panjang kode | varint | Panjang kode model |
| Kode model | k byte | Aliran gabungan semua blok model |
| Blok mentah | sisa file | Semua blok mentah, berurutan |

### Hasil

`Testing/Dialog_Dengan_Jin_Muslim.pdf` (6.877.939 byte):

| Metode | Ukuran | Waktu encode |
|---|---|---|
| `RMF1` (`rmh_final.py`) | 6.352.249 | __WAKTU_LAMA__ |
| **`RMF2` (`rmh_final2.py`)** | **6.121.828** | **35 detik** (+16 detik verifikasi) |
| zip | 6.106.702 | - |
| 7z | 6.059.748 | - |

Rinciannya: header 887 byte + kode model 367.085 byte (1.124.083 byte berpola, konteks orde 5) + blok mentah 5.753.856 byte. Decode butuh 16 detik.

File lain (ukuran dalam byte):

| File | `RMF1` | `RMF2` | Keputusan |
|---|---|---|---|
| `GPU List.txt` | 11.035 | 11.056 | semua blok berpola |
| `NestedRubik256DNA.py` | 13.768 | **13.255** | campuran |
| `123.txt.png` | 8.701 | 8.707 | semua model (hasil pengaman) |
| 100.000 byte acak | 100.040 | 100.056 | campuran (semua mentah) |
| `HoRM.txt` | 1.114 | 1.119 | semua blok berpola |

Untuk file yang seluruhnya berpola, `RMF2` hanya sekitar 5–20 byte lebih besar (peta blok + panjang kode). Untuk file campuran, `RMF2` lebih kecil dan jauh lebih cepat.

### Pengujian

- Encode → decode identik untuk PDF di atas dan semua file uji, termasuk file kosong dan data acak. Encode dua kali menghasilkan file yang sama persis.
- File `RMF1` lama tetap bisa dibuka oleh `rmh_final2.py`.
- 150 uji acak lolos, termasuk ukuran blok 1..4.096, ambang 0..8, dan data campuran acak/teks.
- File rusak ditolak: magic salah, header terpotong, isi terpotong, byte tambahan, peta blok diubah (`Ukuran isi tidak sesuai`), dan isi yang diubah (`SHA-256 tidak cocok`).

### Kenapa masih sedikit di atas zip dan 7z

Sisa selisihnya ada di **struktur teks PDF**. Teks ini penuh potongan panjang yang berulang (sintaks objek PDF, tabel xref). Metode LZ (zip, 7z) menyalin potongan itu sekaligus, sedangkan model konteks menebak byte demi byte. Pada 1.124.083 byte bagian berpola, PPM orde 5 menghasilkan 367.085 byte, sedangkan lzma menghasilkan 291.869 byte. Dengan model salin potongan (LZ), total file diperkirakan sekitar **6.046.612 byte**, lebih kecil dari 7z.


```git
git init
git add .
git commit -m "11 2019, Git @ 04072021 21:47"
git branch -M main
git remote add origin https://github.com/ryanbekabe/Returner-Machine-JupyterLab.git
git push -u origin main

D:\laragon\www\Returner-Machine-JupyterLab>python byteentropy/rmh.py encode Testing/bismillah.txt -o bismillah.rmh
Encode  : Testing/bismillah.txt -> bismillah.rmh (0.000 detik)

Rincian file .rmh:
  header              6 byte
  histogram          14 byte
  crc32               4 byte
  rank                3 byte
  TOTAL              27 byte

Perbandingan ukuran:
  asli                  9 byte
  .rmh                 27 byte  (300.0% dari asli)
  zlib -9              17 byte  (188.9% dari asli)
  lzma -9              68 byte  (755.6% dari asli)
  n*H/8               3.1 byte  (batas Shannon orde-0, n*H/8)

D:\laragon\www\Returner-Machine-JupyterLab>python byteentropy/rmh.py info bismillah.rmh
File .rmh        : bismillah.rmh (27 byte)
Ukuran file asli : 9 byte
Nilai byte unik  : 7
CRC32            : A9420C61
Total permutasi  : 90720
Rank             : 15094
Histogram        :
   97 (0x61) a : 1
   98 (0x62) b : 1
  104 (0x68) h : 1
  105 (0x69) i : 2
  108 (0x6C) l : 2
  109 (0x6D) m : 1
  115 (0x73) s : 1

D:\laragon\www\Returner-Machine-JupyterLab>python byteentropy/rmh.py decode bismillah.rmh -o bismillah_kembali.txt
Decode  : bismillah.rmh -> bismillah_kembali.txt (0.000 detik)
Ukuran  : 9 byte, CRC32 cocok

```git
