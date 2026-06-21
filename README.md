# Analisis Dampak Spasio-Temporal Transisi Energi Industri Nikel Indonesia

Repositori / Direktori ini berisi keseluruhan alur kerja (workflow), data, dan script untuk mereplikasi metodologi abstrak makalah **"Spatio-Temporal Impacts of Energy Transition in Indonesia’s Nickel Processing Industry on Sectoral GRDP: A GTWR and Leontief Input-Output Approach"** karya Anwar Rohmadi, dkk.

## 🗂️ Struktur Folder & File

### 1. Data Sumber (Raw Data)
*   **PDF Reports**: Dokumen riset dari CREA/CELIOS dan IEEFA terkait dampak ekonomi dan emisi gas rumah kaca (GRK) industri nikel.
*   **Abstrak Makalah**: `Anwar Rohmadi_..._APPROACH.docx` (Telah dikonversi ke format `.md`).
*   **CGS Smelter Dataset**: `CGS_Nickel_Smelter_Dataset_V1.xlsx` berisi data 106 smelter nikel beserta koordinat spasial (Latitude/Longitude), proses, kapasitas, dan sumber energi.

### 2. Data Hasil Ekstraksi (`tables_csv/`)
Sebanyak **56 file CSV** berhasil diekstrak dan dibuat, meliputi:
*   Data PDRB Sektoral (Skenario BAU & RE+APC) untuk Sulteng, Sultra, dan Malut.
*   Intensitas GRK dan Bauran Energi dari laporan IEEFA.
*   Data Spasial Smelter yang dikonversi dari file Excel CGS (`CGS_Nickel_Smelter_Dataset.csv`).
*   Estimasi emisi CO₂ per smelter (`CGS_Emission_Estimates.csv`).

### 3. Script Python (Codebase)
*   `extract_pdf_tables.py` & `extract_tables_to_csv.py`: Script untuk mengekstrak 55 tabel dari file PDF menjadi CSV menggunakan `pdfplumber`.
*   `extract_docx_tables.py`: Script ekstraksi tabel dari dokumen Word menggunakan `python-docx` (meski dokumen ternyata tidak memiliki tabel).
*   `estimate_emissions.py`: Script untuk menghitung estimasi emisi CO₂ per smelter. Menggunakan kapasitas energi (*Coal, Diesel, Gas*) dari data CGS yang dikalikan dengan faktor emisi IPCC (0.9 tCO₂/MWh untuk batubara) dan *Capacity Factor* (80%).
*   `build_mastersheet.py`: Script untuk menggabungkan data spasial, data emisi, dan PDRB sektoral (hasil simulasi I-O Leontief) menjadi satu dataset panel berformat CSV (`mastersheet_GTWR.csv`).
*   `run_gtwr.py`: Script utama untuk menjalankan model **Geographically and Temporally Weighted Regression (GTWR)** secara manual menggunakan kernel Gaussian untuk bobot spasial dan temporal.

### 4. Hasil Analisis
*   `kesesuaian_data.md`: Analisis kesesuaian antara ketersediaan data dari ekstraksi dengan kebutuhan data pada abstrak.
*   `mastersheet_GTWR.csv`: Dataset akhir yang diinputkan ke dalam model GTWR.
*   `GTWR_Results.csv`: Prediksi dampak PDRB, nilai residual, dan koefisien spasio-temporal (Beta) lokal untuk 12 kabupaten pada rentang waktu 2020–2035.
*   `GTWR_Summary.csv`: Ringkasan statistik performa model GTWR.

---

## 🔄 Alur Percakapan dan Workflow (Walkthrough)

### Fase 1: Ekstraksi Data PDF ke CSV
*   **Permintaan:** Pengguna meminta ekstraksi tabel dari laporan PDF CREA/CELIOS dan IEEFA.
*   **Tindakan:** Dibuat script `extract_tables_to_csv.py` menggunakan pustaka `pdfplumber`. Hasilnya, 55 tabel terekstrak dengan rapi dan disimpan di folder `tables_csv/`.

### Fase 2: Pengecekan Dokumen DOCX
*   **Permintaan:** Pengguna meminta ekstraksi tabel dari makalah Anwar Rohmadi format `.docx`.
*   **Tindakan:** Dibuat script `extract_docx_tables.py`, namun gagal menemukan tabel. Setelah dibedah struktur XML-nya, terbukti bahwa dokumen tersebut hanya berisi **10 paragraf teks abstrak** tanpa ada tabel satupun.

### Fase 3: Analisis Gap Data (Kesesuaian Data)
*   **Permintaan:** Pengguna menanyakan apakah 55 data CSV tadi cocok dengan kebutuhan abstrak penelitian.
*   **Tindakan:** Dilakukan analisis kesesuaian data. Ditemukan bahwa 55 tabel CSV **Sangat Cocok** untuk PDRB, Intensitas Emisi, dan Kapasitas. Namun, ada GAP (kekurangan) pada **Data Koordinat Spasial** (Latitude/Longitude) yang krusial untuk metode GTWR. Tingkat kesesuaian saat itu adalah ~65%.

### Fase 4: Integrasi CGS Dataset (Penyelesaian Gap Data)
*   **Permintaan:** Pengguna memberikan file `CGS_Nickel_Smelter_Dataset_V1.xlsx`.
*   **Tindakan:** File Excel diekstrak. File ini ternyata adalah **kepingan data yang hilang** karena memuat koordinat Latitude/Longitude, Kapasitas Pembangkit (MW), dan Status 106 Smelter. Tingkat kesesuaian data naik menjadi ~90%.

### Fase 5: Estimasi Emisi dan Pembuatan Mastersheet
*   **Permintaan:** Pengguna bertanya opsi pengganti untuk data emisi aktual yang sulit dicari.
*   **Tindakan:** Diusulkan metode estimasi emisi menggunakan rumus *IPCC Emission Factor* sebagai proksi yang dihitung berdasarkan kapasitas *captive power* di tiap smelter (Script `estimate_emissions.py`). Setelah itu, dibuat script `build_mastersheet.py` untuk mengawinkan data Spasial, Emisi, dan PDRB ke dalam format panel regresi (`mastersheet_GTWR.csv`).

### Fase 6: Eksekusi Model GTWR
*   **Permintaan:** Pengguna meminta eksekusi model GTWR beserta Mastersheet-nya.
*   **Tindakan:** Dibuat script `run_gtwr.py` yang mengimplementasikan regresi berbobot geografis dan temporal (GTWR). Script mencari *bandwidth* optimal melalui *Cross-Validation* dan menghasilkan keluaran koefisien Beta lokal.
*   **Hasil Akhir:** Model menunjukkan nilai $R^2 = 0.4273$, membuktikan bahwa emisi CO₂ memiliki dampak negatif (koefisien Beta rata-rata = -3.24) terhadap PDRB wilayah yang didominasi oleh smelter dengan skenario *Business as Usual*.

---
*Catatan Dokumentasi: Dibuat secara otomatis oleh Antigravity Assistant.*
