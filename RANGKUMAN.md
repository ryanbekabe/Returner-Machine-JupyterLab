# Rangkuman Diskusi Return[er] Machine

Catatan perjalanan pengembangan, dari setup workspace sampai enumerative coding per blok. Detail cara pakai tiap script ada di [README.md](README.md).

Prinsip kerja selama diskusi: **file yang sudah ada tidak diubah**. Setiap perbaikan atau tahap baru dibuat sebagai program baru.

---

## 1. Setup workspace

- Semua `import` di file `.py` dan `.ipynb` dianalisis untuk menyusun daftar dependensi.
- Dibuat `Testing/requirements.txt` (paket inti: jupyterlab, numpy, matplotlib, opencv-python, numba, pandas, pillow, pefile, geopy, scikit-learn) dan `Testing/requirements-optional.txt` (tensorflow, keras, cupy, efficientnet, livelossplot untuk notebook GPU).
- Ditemukan beberapa masalah di kode lama:
  - `from polynomial import polynomial` di `Permutasi.ipynb` bukan paket pip.
  - Beberapa notebook memakai API lama yang sudah dihapus (`keras.layers.embeddings`, `sklearn.externals.joblib`).
  - `suffix_arrays.ipynb` diawali komentar `//` sehingga bukan JSON valid.

## 2. Konsep dasar

### Rubik 4×4

- **96 stiker** (6 sisi × 16).
- **56 kepingan fisik**: 8 sudut + 24 tepi + 24 tengah. (4×4×4 = 64, dikurangi 8 kubus dalam yang tidak ada.)

### Byte, histogram, entropy

- Satu byte bernilai **0..255** (256 kemungkinan), bukan 0..256.
- **Setiap file**, teks maupun biner, adalah deretan byte 0..255. Bedanya hanya pada cara byte itu ditafsirkan.
- **Byte histogram** = frekuensi tiap nilai byte 0..255 (256 angka).
- **Byte entropy (Shannon)** = satu angka yang dihitung dari histogram: `H = -Σ p·log2(p)`, rentang 0..8 bit/byte.
- `n × H / 8` = batas bawah ukuran kompresi jika tiap byte diperlakukan independen (orde-0).

### Perbaikan `histogram.py` → `byteentropy/histogram_v2.py`

- Di versi lama, `Index ke - i` hanya nomor urut `Counter`, bukan nilai byte. Versi baru memakai nilai byte 0..255 sebagai index.
- Tambahan: opsi `--semua`, `--plot`, dukungan nama file berspasi, dan pesan error yang jelas.

## 3. Masalah utama: histogram kehilangan urutan

Histogram hanya mencatat **berapa kali**, bukan **di mana**. Banyak data berbeda punya histogram yang sama:

```
jumlah susunan = n! / (c1! · c2! · ... · ck!)
```

| Data | Susunan dengan histogram sama |
|---|---|
| `bismill` (7 byte) | 1.260 |
| `bismillah` (9 byte) | 90.720 |

`bismill` dan `ismillb` tidak bisa dibedakan dengan permutasi saja.

### Percobaan: tanda posisi awal dan akhir

| Tanda | Kandidat tersisa |
|---|---|
| tanpa tanda | 1.260 |
| awal `b` + akhir `l` | 60 |
| awal `bi` + akhir `ll` | 6 |
| awal `bis` + akhir `ill` | 1 |

Kandidat baru tinggal 1 setelah 6 dari 7 byte ditandai. Itu sama saja dengan menyimpan data aslinya.

## 4. Solusi: enumerative coding (histogram + rank)

Semua susunan diurutkan berdasarkan nilai byte, lalu yang disimpan adalah **histogram + nomor urut (rank)** data asli.

| Data | Rank | Bit untuk rank |
|---|---|---|
| `bismill` | 57 | 11 |
| `ismillb` | 533 | 11 |
| `bismillah` | 15.094 dari 90.720 | 17 |

- Decode **tanpa brute force**: byte yang tepat dihitung langsung di setiap posisi.
- Script demonstrasi: `byteentropy/permutasi_rank.py`.
- **Inilah metode yang dicari** untuk Return[er] Machine.

## 5. Tahap "Simpan ke file": format `.rmh`

Script `byteentropy/rmh.py` (perintah `encode`, `decode`, `info`).

Struktur file: magic `RMH1` + ukuran asli + histogram + CRC32 + rank. Panjang rank tidak disimpan karena bisa dihitung dari histogram.

Contoh `bismillah.rmh` (27 byte):

```
52 4D 48 31                 magic "RMH1"
09 07                       ukuran = 9, byte unik = 7
61 01 62 01 68 01 69 02     a=1 b=1 h=1 i=2
6C 02 6D 01 73 01           l=2 m=1 s=1
A9 42 0C 61                 CRC32
00 3A F6                    rank = 15094
```

Hasil penting:

| File | Asli | .rmh | lzma |
|---|---|---|---|
| `HoRM.txt` | 4.690 | 2.243 | 1.024 |
| `RMHash_HoRM2.txt` | 8.585 | 4.043 | 584 |
| `123.txt.png` | 10.073 | 10.287 | 8.264 |

- Ukuran `.rmh` selalu mendekati batas Shannon orde-0, jadi metodenya bekerja optimal untuk pendekatan berbasis frekuensi.
- lzma lebih kecil pada teks karena memanfaatkan urutan dan pengulangan.
- Kelemahan: **kecepatan kuadratik**. File 50 KB butuh sekitar 3 detik, 136 KB butuh 21,6 detik.

## 6. Tahap "Per blok": format `.rmb`

Script `byteentropy/rmh_blok.py` (perintah `encode`, `decode`, `info`, `analisis`).

- File dipecah menjadi blok (default 4.096 byte). Setiap blok punya histogram + rank sendiri.
- Waktu proses turun dari n² menjadi n × B (linear), dan blok bisa diproses paralel.

`Testing/GPU List.txt` (136.412 byte ≈ 133 KB):

| Metode | Encode | Ukuran |
|---|---|---|
| `rmh.py` tanpa blok | 21,6 detik | 88.067 byte |
| per blok, 1 core | 0,81 detik | 89.892 byte |
| per blok, 16 core | 0,23 detik | 89.892 byte |

- File tersebut menjadi **34 blok**: 33 × 4.096 + 1 × 1.244 = 136.412 byte. Semua blok tetap berada di dalam **satu file** `.rmb`.
- Tarik-ulur ukuran blok: blok kecil membuat rank lebih kecil tetapi histogram membengkak; blok besar membuat proses lambat. Untuk file ini, 4.096–16.384 byte adalah titik tengah yang baik.
- Kolom Panjang, Byte unik, Rank (byte), dan Entropy di `info` **dihitung saat ditampilkan**, tidak disimpan di file. Yang tersimpan per blok hanya histogram + rank.

## 7. Ide: blok yang terbuka memberi informasi blok berikutnya

Pertanyaan: bisakah 1–5 blok cukup untuk file berapa pun besarnya, karena setiap blok yang terbuka memberi tahu isi blok berikutnya?

### Tidak mungkin untuk semua file

Decode bersifat pasti dan tidak bisa menciptakan informasi baru.

```
File berbeda berukuran 136.412 byte = 256^136.412
Isi berbeda dari 5 blok × 4.096 byte = 256^20.480
```

Wadah kecil tidak bisa membedakan semua file besar (prinsip sarang merpati). Pengecualiannya adalah file yang **berpola**, misalnya `nullbyte.txt` atau fraktal seperti `sierpinski.jpg`, yang bisa dibangkitkan dari aturan kecil (kompleksitas Kolmogorov).

### Mungkin: pemodelan adaptif

Isi yang sudah terbuka dipakai untuk **menebak** isi berikutnya. Encoder dan decoder melihat data yang sama, jadi tebakannya tidak perlu disimpan. Yang disimpan hanya selisih dari tebakan.

Ukuran informasi minimum `GPU List.txt` berdasarkan jumlah byte sebelumnya yang dipakai sebagai petunjuk (batas optimistis, belum termasuk biaya model):

| Petunjuk | Ukuran |
|---|---|
| tanpa petunjuk (orde-0, `.rmb` sekarang) | 87.903 byte |
| 1 byte sebelumnya (orde-1) | 35.794 byte |
| 2 byte sebelumnya (orde-2) | 13.773 byte |
| 3 byte sebelumnya (orde-3) | 8.546 byte |
| *lzma* | *9.024 byte* |

## 8. Langkah 1 selesai: histogram adaptif (`.rma`)

Script `byteentropy/rmh_adaptif.py` (perintah `encode`, `decode`, `bandingkan`).

- Histogram **tidak disimpan**. Histogram dipelajari dari byte yang sudah terbuka: mulai dari frekuensi 1 untuk semua byte, +32 setiap kali byte muncul, dan dibagi dua saat total melewati 65.536.
- Rank dihitung bertahap per byte dengan arithmetic coding 32-bit, jadi waktunya linear.
- Terbukti: model adaptif +1 menghasilkan bit yang **persis sama** dengan `nomor histogram + rank` (18.596,771 bit pada `HoRM.txt`). Model adaptif adalah enumerative coding dengan histogram yang dikodekan secara implisit.

| File | `.rmb` | `.rma` | lzma |
|---|---|---|---|
| `GPU List.txt` (136.412) | 89.892 | 87.387 | 9.024 |
| `NestedRubik256DNA.py` (15.112) | 15.745 | 14.484 | 12.208 |
| `123.txt.png` (10.073) | 11.030 | 10.086 | 8.264 |

`GPU List.txt` di-encode dalam 0,53 detik dan di-decode dalam 0,68 detik dengan 1 core.

## 9. Langkah 2 selesai: konteks PPM (`.rmk`)

Script `byteentropy/rmh_konteks.py` (perintah `encode`, `decode`, `bandingkan`).

- Satu histogram adaptif **per konteks** (1..N byte sebelumnya), tetap tidak disimpan di file.
- PPM: coba konteks terpanjang. Jika byte belum pernah muncul di sana, kirim ESCAPE dan turun ke konteks lebih pendek, sampai orde −1 (256 byte berpeluang sama). Byte yang sudah gagal dikecualikan.
- Pada `GPU List.txt` dengan orde 3, 95,6% byte berhasil ditebak dari 3 byte sebelumnya.

| File | `.rma` | `.rmk` (orde terbaik) | zlib | lzma |
|---|---|---|---|---|
| `GPU List.txt` (136.412) | 87.387 | **11.006** (orde 5) | 11.285 | 9.024 |
| `HoRM.txt` (4.690) | 2.119 | **1.085** (orde 3) | 1.236 | 1.024 |
| `RMHash_HoRM2.txt` (8.585) | 3.878 | **975** (orde 3) | 1.146 | 584 |

- `.rmk` mengalahkan zlib pada ketiga file di atas, dan mendekati lzma.
- lzma masih unggul pada data yang sangat berulang, karena bisa menyalin potongan panjang sekaligus.

## 10. Melihat isi file `.rmk`

Script `byteentropy/rmh_konteks_info.py`, padanan `rmh_blok.py info` untuk `.rmk`.

- File `.rmk` hanya berisi header (12 byte untuk `GPU List.txt`), CRC32, dan satu deretan bit kode. **Histogram/konteks: 0 byte.**
- Karena tidak ada yang disimpan, info didapat dengan **memutar ulang decode** sambil mencatat orde yang menebak, jumlah ESCAPE, dan biaya bit setiap kejadian `log2(total / lebar interval)`.
- Output: isi file, rincian per segmen, ke mana bit dihabiskan, konteks yang dipelajari, dan jejak decode (`--jejak`).

Temuan dari `GPU List.txt`:

- Segmen 0 paling mahal (614,8 byte) karena model masih belajar. Segmen berikutnya hanya sekitar 300–400 byte. Di `.rmb`, setiap blok butuh sekitar 2.500 byte karena selalu mulai dari nol.
- Byte yang tertebak di orde 3 rata-rata hanya 0,49 bit. ESCAPE memakan 14% kode.
- Contoh konteks yang dipelajari: setelah `tio` selalu muncul `n` (2.878 kali), dari kata `option`.

Temuan dari `Testing/logfactorial.txt` (5,6 MB):

| zlib -9 | lzma -9 | `.rmk` orde 3 |
|---|---|---|
| 2.413.002 | 2.270.136 | **2.130.339** |

- Pertama kalinya `.rmk` **mengalahkan lzma** pada file nyata. Setelah konteks `000`, byte berikutnya hampir pasti `0`, jadi deretan nol hampir gratis. Digit lainnya tersebar merata dan memang tidak bisa diperkecil di bawah sekitar 3,32 bit.
- Rata-rata 3,02 bit per byte. Memutar ulang decode file ini butuh sekitar 43 detik.

## 11. Ukuran hasil dan istilah ekstensi

- Ukuran hasil mengikuti **informasi baru**, bukan ukuran file. 100.000 byte nol menjadi 18 byte, sedangkan 100.000 byte acak tetap sekitar 100.000 byte.
- Ekstensi: **rm** = Returner Machine, lalu huruf tahapnya: `.rmh` Hash, `.rmb` Blok, `.rma` Adaptif, `.rmk` Konteks, `.rmf` Final.

## 12. Versi final: `.rmf`

Pertanyaan: metode mana yang paling kecil dan tetap bisa digenerate kembali, konsisten seperti hash?

- **Konteks** paling kecil untuk data berpola. **Adaptif** atau **mentah** paling cocok untuk data acak atau yang sudah terkompresi. Keempat metode lossless dan deterministik.
- Ukuran hasil yang selalu tetap untuk semua file **tidak mungkin** (prinsip sarang merpati). Solusinya, dua peran dipisah: **SHA-256** sebagai identitas berukuran tetap (32 byte), dan **kode** sebagai resep untuk membangun kembali file-nya.

Script `byteentropy/rmh_final.py` (perintah `encode`, `decode`, `info`):

- Menguji mentah, adaptif, dan konteks orde 1–5, lalu memilih yang terkecil. File di atas 256 KB diuji memakai sampel 3 × 64 KB.
- Jika hasilnya tidak lebih kecil dari asli, file disimpan mentah, sehingga tidak pernah membengkak.
- SHA-256 di header. Encode langsung diverifikasi dengan decode ulang.
- Deterministik: encode dua kali menghasilkan file yang sama persis.

| File | Asli | Mode terpilih | `.rmf` |
|---|---|---|---|
| `GPU List.txt` | 136.412 | konteks orde 5 | 11.035 |
| `logfactorial.txt` | 5.644.322 | konteks orde 3 | 2.130.368 |
| 100.000 byte acak | 100.000 | mentah | 100.040 |

## 13. Mode campuran per blok: `.rmf` versi 2

Masalah: `Dialog_Dengan_Jin_Muslim.pdf` (6,9 MB) lambat dan hasilnya lebih besar dari zip dan 7z. Sebanyak 87% isi PDF sudah terkompresi (gambar JPEG dan Flate), dan model konteks memperbesar data seperti ini sambil berjalan lambat.

Script `byteentropy/rmh_final2.py`, format `RMF2`:

- File dibagi per blok 1.024 byte. Blok dengan entropy di atas 7,6 bit/byte disimpan **mentah**. Blok lainnya digabung dan dikodekan dengan mode terbaik.
- Pengaman: "campuran" dibandingkan dengan "semua model", supaya file seperti PNG tidak dirugikan.
- Peta blok (1 bit per blok) disimpan di header. `rmh_final2.py` tetap bisa membuka `RMF1`.

| `Dialog_Dengan_Jin_Muslim.pdf` | Ukuran | Encode |
|---|---|---|
| `RMF1` | 6.352.249 | sekitar 7,5 menit |
| **`RMF2`** | **6.121.828** | **35 detik** |
| zip | 6.106.702 | |
| 7z | 6.059.748 | |

Sisa selisih dengan zip/7z ada di struktur teks PDF yang penuh potongan berulang. Dengan model salin potongan (LZ), total diperkirakan 6.046.612 byte, lebih kecil dari 7z.

## 14. Memangkas biaya ESCAPE: `.rmk` versi 2

Pertanyaan: bisakah biaya ESCAPE, yang memakan 14% kode, dipangkas?

- **Jumlah** ESCAPE tidak bisa dikurangi, karena ESCAPE terjadi setiap kali byte belum pernah muncul di konteks itu. `GPU List.txt` orde 5 tetap 7.586 ESCAPE. Yang bisa dipangkas adalah **harga** setiap ESCAPE dan setiap byte.
- Sebelum menulis program, beberapa ide diukur dulu dengan simulasi ukuran ideal (jumlah −log₂ p). Simulasi ini cocok dengan `.rmk` asli: 10.994 lawan 11.006 byte, dan selisih 12 byte itu header.

| Ide | Hasil simulasi |
|---|---|
| **SEE** (Secondary Escape Estimation): peluang ESCAPE dipelajari dari pengalaman, bukan dihitung dengan rumus tetap PPM-D | 3–8% lebih kecil |
| **Update exclusion**: frekuensi hanya ditambah di orde yang menebak dan orde di atasnya | 3–12% lebih kecil |
| Keduanya | 7–23% lebih kecil |
| Warisan statistik dari konteks induk (versi sederhana) | justru 1–3% lebih **besar**, tidak dipakai |

- Persentase ESCAPE bukan target yang tepat. Pada `GPU List.txt` orde 5, porsinya justru naik dari 14,5% ke 17,6% setelah SEE ditambahkan, karena byte biasa menjadi jauh lebih murah. Yang penting adalah ukuran total.

Script `byteentropy/rmh_konteks2.py` (perintah `encode`, `decode`, `bandingkan`), format `RMK2`. Tabel SEE dipelajari bersama oleh encoder dan decoder, jadi tidak disimpan di file. Semua hitungan memakai bilangan bulat.

| File | RMK1 | **RMK2** | zlib | lzma |
|---|---|---|---|---|
| `GPU List.txt` (136.412) | 11.006 | **9.630** | 11.285 | 9.024 |
| `HoRM.txt` (4.690) | 1.085 | **922** | 1.236 | 1.024 |
| `RMHash_HoRM2.txt` (8.585) | 975 | **753** | 1.146 | 584 |
| `Return[er]Machine.py` (7.235) | 2.174 | **1.911** | 2.103 | 2.168 |
| `NestedRubik256DNA.py` (15.112) | 13.739 | **12.319** | 12.354 | 12.208 |
| `123.txt.png` (10.073) | 8.672 | **8.054** | 8.369 | 8.264 |
| `logfactorial.txt` (5.644.322) | 2.130.339 | **2.125.017** | 2.413.002 | 2.270.136 |

- RMK2 lebih kecil dari RMK1 pada semua file uji. RMK2 mengalahkan zlib **dan** lzma pada `HoRM.txt`, `Return[er]Machine.py`, dan `123.txt.png`.
- lzma masih unggul pada data yang sangat berulang. Celahnya pada `GPU List.txt` mengecil dari 1.982 menjadi 606 byte.
- `rmh_konteks2.py decode` juga bisa membuka file `RMK1`.

---

## Daftar file yang dibuat

| File | Fungsi |
|---|---|
| `Testing/requirements.txt` | Dependensi inti |
| `Testing/requirements-optional.txt` | Dependensi GPU / deep learning |
| `.gitignore` | Mengabaikan `.venv/` dan `__pycache__/` |
| `byteentropy/histogram_v2.py` | Histogram + entropy versi perbaikan |
| `byteentropy/permutasi_rank.py` | Demonstrasi enumerative coding di memori |
| `byteentropy/rmh.py` | Encode/decode file `.rmh` |
| `byteentropy/rmh_blok.py` | Encode/decode file `.rmb` per blok, paralel |
| `byteentropy/rmh_adaptif.py` | Encode/decode file `.rma`, histogram adaptif |
| `byteentropy/rmh_konteks.py` | Encode/decode file `.rmk`, konteks PPM |
| `byteentropy/rmh_konteks_info.py` | Melihat isi file `.rmk` dengan memutar ulang decode |
| `byteentropy/rmh_final.py` | Encode/decode `.rmf` versi 1, mode otomatis + SHA-256 |
| `byteentropy/rmh_final2.py` | **Versi yang disarankan**: `.rmf` versi 2, mode campuran per blok |
| `byteentropy/rmh_konteks2.py` | Encode/decode `.rmk` versi 2: PPM + SEE + update exclusion |

## Langkah berikutnya

1. ~~**Histogram adaptif.**~~ Selesai, lihat bagian 8.
2. ~~**Konteks orde-1/orde-2.**~~ Selesai, lihat bagian 9. Hasilnya melampaui perkiraan: `GPU List.txt` turun menjadi 11 KB dengan orde 5.
3. **Context mixing.** Menggabungkan tebakan beberapa orde sekaligus (seperti PAQ/cmix), bukan memilih satu lewat escape. Langkah antara sudah selesai: biaya ESCAPE dipangkas dengan SEE dan update exclusion (bagian 14). `rmh_final2.py` belum memakai RMK2.
4. **Model salin potongan (LZ).** Untuk data yang sangat berulang, di mana lzma masih unggul. Prioritas berikutnya: diperkirakan membuat PDF uji lebih kecil dari 7z.
5. **Percepatan.** Python murni sekitar 100 KB/detik. Perlu numba atau C/Rust untuk file berukuran MB.
