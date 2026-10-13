
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
- Saat ini script hanya mendemonstrasikan encode → decode di memori. Script belum menyimpan histogram + rank ke file.


```git
git init
git add .
git commit -m "11 2019, Git @ 04072021 21:47"
git branch -M main
git remote add origin https://github.com/ryanbekabe/Returner-Machine-JupyterLab.git
git push -u origin main

```git
