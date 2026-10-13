
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
pip install -r requirements.txt

# (Opsional) TensorFlow/Keras/CuPy untuk numba-cuda-stencil.ipynb, butuh GPU NVIDIA + CUDA
pip install -r requirements-optional.txt

# 4. Jalankan JupyterLab
jupyter lab
```

Menjalankan script Python langsung, misalnya:

```bash
python "Return[er]Machine.py"             # input diatur lewat variabel namafilenya di dalam script
python byteentropy/histogram.py <nama_file>
```


```git
git init
git add .
git commit -m "11 2019, Git @ 04072021 21:47"
git branch -M main
git remote add origin https://github.com/ryanbekabe/Returner-Machine-JupyterLab.git
git push -u origin main

```git
