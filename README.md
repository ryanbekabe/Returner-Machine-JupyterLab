
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

Waktu naik kira-kira kuadratik terhadap ukuran file, karena rank adalah satu bilangan bulat raksasa yang ikut dihitung ulang di setiap posisi. Script memberi peringatan untuk file di atas 20.000 byte. Solusinya adalah memecah file per blok (tahap berikutnya).


```git
git init
git add .
git commit -m "11 2019, Git @ 04072021 21:47"
git branch -M main
git remote add origin https://github.com/ryanbekabe/Returner-Machine-JupyterLab.git
git push -u origin main

```git
