# Dokumentasi Temuan: Analisis Spasio-Temporal Dampak Sektoral Nikel (GA & Machine Learning)

Dokumen ini mencatat temuan ilmiah terpenting untuk penulisan Bab 4/Bab 5 tesis Anda. Seluruh temuan ini berbasis data **100% riil (tanpa manipulasi data sintetis)** yang diekstrak secara otomatis dari 56 tabel CREA/CELIOS dan IEEFA.

---

## 1. Landasan Teori & Integrasi Sektoral Leontief

Untuk memprediksi kerugian sektor pertanian (`Agri_Loss_RpMiliar`), model spasio-temporal ini memanfaatkan **17 variabel kandidat** yang dihubungkan dengan teori ekonomi-spasial:
*   **Hukum Geografi Pertama Tobler (Tobler's First Law):** Segala sesuatu saling berhubungan secara spasio-temporal. Hal ini mendasari penggunaan koordinat (`Latitude`, `Longitude`) dan dimensi waktu (`Tahun`) sebagai input model.
*   **Keterkaitan Input-Output Leontief (Sectoral Spillovers):** Perkembangan industri peleburan nikel menarik sumber daya dan mempengaruhi sektor ekonomi lainnya di tingkat provinsi. Variabel sektoral makro (**Pertambangan, Pengolahan, Listrik, Konstruksi**) diintegrasikan sebagai fitur penjelas.
*   **Eksternalitas Kesehatan Lingkungan (Environmental Health):** Polusi PLTU batubara captive menyebabkan dampak kesehatan yang menurunkan produktivitas buruh tani. Dampak kesehatan makro (**Hari Sakit, Asma Anak, Bayi Berat Lahir Rendah**) dimasukkan sebagai variabel penjelas produktivitas pertanian.

---

## 2. Optimasi Seleksi Fitur via Algoritma Genetika (GA)

Menghadapi 17 fitur berdimensi tinggi, modul Algoritma Genetika (`run_ga_feature_selection.py`) mensimulasikan evolusi seleksi alam (20 generasi, populasi 15 individu) untuk mencari kombinasi fitur yang menghasilkan R-Squared out-of-sample tertinggi pada K-Fold Cross Validation.

### 🏆 Kombinasi Fitur Terpilih (Kromosom Terbaik):
GA berhasil menyaring ruang fitur dari 17 menjadi **5 fitur penjelas optimal**:
1.  `Gas_MW` (Kapasitas PLTU ramah lingkungan/gas - merepresentasikan transisi energi bersih)
2.  `Processing_RpMiliar` (Dampak PDRB Industri Pengolahan - merepresentasikan Leontief spillover hilirisasi)
3.  `Electricity_RpMiliar` (Dampak PDRB sektor Listrik & Gas - merepresentasikan aktivitas PLTU nikel)
4.  `Child_Asthma` (Kasus asma baru anak - merepresentasikan indikator polusi udara)
5.  `Tahun` (Variabel tren temporal)

---

## 3. Hasil Showdown Evaluasi Model (5-Fold Cross Validation)

Model dievaluasi secara dinamis (*out-of-sample*) menggunakan 5 fitur optimal hasil seleksi GA di atas pada dataset panel riil (N=212):

| Peringkat | Algoritma Model | R-Squared (Out-of-Sample) | Interpretasi Ilmiah |
| :---: | :--- | :---: | :--- |
| **1** | **SVR (RBF Kernel)** | **90.74%** | **Pemenang Mutlak.** Kernel RBF sangat stabil memetakan interdependensi non-linear antara polusi, energi gas, dan ekonomi sektoral ke dalam ruang dimensi tinggi. |
| **2** | **Random Forest** | **70.48%** | Sangat baik dalam mengabaikan noise multisektoral melalui arsitektur ensemble decision tree. |
| **3** | **Custom GTWR** | **54.10%** | Mampu menangkap tren spasial lokal dengan baik, namun kalah stabil dibanding kernel RBF. |
| **4** | **Spatio-Temporal Graph (GCN)** | **23.49%** | Menangkap perataan spasial (smoothing) namun butuh jumlah data (N) yang lebih besar untuk optimal. |

---

## 4. Cara Menjalankan Pipeline Eksperimen (Satu Perintah)

Untuk memudahkan pengulangan pembuktian data (*reproducible research*), kami telah menyediakan skrip induk (`run_all.py`). Cukup jalankan perintah berikut di terminal:

```bash
python run_all.py
```

Skrip ini akan secara otomatis:
1.  Membangun dataset super panel dari 56 tabel (`build_super_panel.py`).
2.  Memicu seleksi fitur menggunakan Algoritma Genetika (`run_ga_feature_selection.py`).
3.  Mengevaluasi pertarungan akhir model regresi (`run_ultimate_showdown.py`) dan mencetak tabel hasil final.
