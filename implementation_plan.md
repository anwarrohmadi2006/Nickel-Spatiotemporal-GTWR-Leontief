# Rencana Implementasi: Seleksi Fitur Berbasis Algoritma Genetika & Teori Spasio-Temporal

Rencana ini merancang integrasi yang jauh lebih masif dari 56 tabel CREA/IEEFA, melahirkan **17 variabel kandidat** (spasial, teknologi, sektoral ekonomi Leontief, dan kesehatan), serta membuat modul **Algoritma Genetika (GA)** untuk menyeleksi kombinasi fitur terbaik demi memprediksi kerugian sektor pertanian (`Agri_Loss_RpMiliar`).

## 1. Landasan Teori yang Disesuaikan

Untuk memastikan hasil pemodelan memiliki nilai akademis tinggi bagi tesis Anda, fitur-fitur baru ini akan dikaitkan langsung dengan tiga teori utama:

1.  **Hukum Pertama Geografi Tobler (Tobler's First Law)**:
    *   *Aplikasi:* Penggunaan koordinat (`Latitude`, `Longitude`) dan bobot spasial Gaussians (`sw`) untuk membagikan dampak makro ke tingkat mikro smelter.
2.  **Analisis Input-Output Leontief (Sektoral Linkages)**:
    *   *Aplikasi:* Memasukkan output dari sektor **Pertambangan, Industri Pengolahan, Listrik & Gas, serta Konstruksi** sebagai fitur. Pertumbuhan sektor industri nikel secara langsung menekan/menarik sumber daya dari sektor primer (Pertanian) melalui hubungan input-output.
3.  **Teori Kesehatan Lingkungan & Produktivitas**:
    *   *Aplikasi:* Memasukkan dampak kesehatan makro (**Hari Sakit, Kasus Asma Anak, Berat Bayi Lahir Rendah**) yang didownscale ke tingkat smelter. Polusi dari batubara captive mengurangi jam kerja efektif petani, memperparah kerugian ekonomi pertanian.

---

## 2. Fitur Baru yang Akan Diekstrak dari 56 Tabel

Kami akan memperluas `build_super_panel.py` untuk mengekstrak variabel berikut:

### A. Dimensi Ekonomi Sektoral Leontief (CREA Table 06, 08, 10, 12, 14, 16)
*   `Mining_RpMiliar`: Dampak PDRB sektor Pertambangan & Penggalian.
*   `Processing_RpMiliar`: Dampak PDRB sektor Industri Pengolahan (Smelter).
*   `Electricity_RpMiliar`: Dampak PDRB sektor Pengadaan Listrik & Gas (PLTU Captive).
*   `Construction_RpMiliar`: Dampak PDRB sektor Konstruksi.

### B. Dimensi Dampak Kesehatan (CREA Table 19)
*   `Work_Absence`: Hari cuti/sakit akibat polusi udara.
*   `Child_Asthma`: Kasus asma baru pada anak-anak.
*   `Low_Birth_Weight`: Kasus bayi dengan berat lahir rendah.

### C. Dimensi Spesifikasi Teknologi Smelter (CGS Dataset)
*   `Diesel_MW`, `PLN_MW`, `Gas_MW`, `Hydro_MW` (tambahan di samping `Capacity_tpa` dan `Coal_MW`).

---

## 3. Alur Algoritma Genetika (GA) untuk Seleksi Fitur

Kami akan membuat skrip baru `run_ga_feature_selection.py` dengan logika sebagai berikut:
1.  **Representasi Kromosom:** Vector biner berukuran $17$ (sesuai jumlah fitur). Angka `1` berarti fitur aktif, `0` berarti non-aktif.
2.  **Fungsi Kebugaran (Fitness Function):** Nilai out-of-sample $R^2$ dari 5-Fold Cross Validation menggunakan model regresi (Random Forest).
3.  **Operasi Genetika:**
    *   *Seleksi:* Tournament Selection (memilih induk terbaik).
    *   *Crossover:* Single-point crossover untuk pertukaran bit fitur.
    *   *Mutasi:* Bit-flip mutation dengan probabilitas rendah (misal 5%) untuk menjaga keberagaman fitur.
    *   *Elitisme:* Mempertahankan kromosom terbaik dari generasi sebelumnya.
4.  **Generasi:** Berjalan selama 20 generasi dengan populasi 15 individu untuk menemukan subset fitur optimal.

---

## 4. Rincian Perubahan Kode

### [MODIFY] [build_super_panel.py](file:///c:/Users/msi/Documents/New%20folder/Nickel-Spatiotemporal-GTWR-Leontief/build_super_panel.py)
*   Menambahkan parsing untuk kolom sektor lain (Pertambangan, Pengolahan, Listrik, Konstruksi) pada 6 file CREA.
*   Menambahkan parsing untuk dampak kesehatan dari file `CREA_CELIOS_Table19*.csv`.
*   Menambahkan kolom daya listrik non-batubara (`Diesel_MW`, `PLN_MW`, `Gas_MW`, `Hydro_MW`).
*   Mengekspor dataset baru ke `SpatioTemporal_SuperPanel_Enriched.csv`.

### [NEW] [run_ga_feature_selection.py](file:///c:/Users/msi/Documents/New%20folder/Nickel-Spatiotemporal-GTWR-Leontief/GTWR_Experiment_V2/run_ga_feature_selection.py)
*   Modul Algoritma Genetika yang mencari kombinasi dari 17 fitur di atas yang menghasilkan prediksi `Agri_Loss_RpMiliar` paling akurat.

### [MODIFY] [run_ultimate_showdown.py](file:///c:/Users/msi/Documents/New%20folder/Nickel-Spatiotemporal-GTWR-Leontief/GTWR_Experiment_V2/run_ultimate_showdown.py)
*   Memuat dataset yang telah diperkaya (`SpatioTemporal_SuperPanel_Enriched.csv`).
*   Menggunakan fitur terpilih hasil seleksi GA untuk melatih model Random Forest, SVR, GCN, dan GTWR.

---

## 5. Rencana Verifikasi

### Automated Verification
*   Jalankan `python build_super_panel.py` untuk memastikan ekstraksi 17 variabel baru dari file-file CSV berjalan lancar.
*   Jalankan `python GTWR_Experiment_V2/run_ga_feature_selection.py` untuk melihat proses optimasi GA dan mencatat subset fitur terbaik.
*   Jalankan `python GTWR_Experiment_V2/run_ultimate_showdown.py` untuk membandingkan R-squared model showdown pada fitur hasil optimasi GA.
