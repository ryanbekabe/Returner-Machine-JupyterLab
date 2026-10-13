
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


```git
git init
git add .
git commit -m "11 2019, Git @ 04072021 21:47"
git branch -M main
git remote add origin https://github.com/ryanbekabe/Returner-Machine-JupyterLab.git
git push -u origin main

```git
