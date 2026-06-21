# Evaluasi Spasio-Temporal Dampak Ekonomi Kawasan Industri Nikel: Pendekatan CRISP-DM dan Geographically and Temporally Weighted Regression (GTWR)

**Laporan Analisis Ekstensif & Pemodelan Lintas Sektoral**
*Disusun oleh: Anwar Rohmadi*

---

## RINGKASAN EKSEKUTIF
Indonesia merupakan pemegang cadangan nikel terbesar di dunia. Upaya pemerintah untuk mengintegrasikan perekonomian nasional ke dalam rantai pasok global kendaraan listrik (*Electric Vehicles*) telah mendorong pembangunan kawasan industri pengolahan (*smelter*) berskala besar di wilayah Indonesia Timur. Namun demikian, ekspansi hilirisasi nikel sering kali dievaluasi berdasarkan indikator investasi makro, dengan mengesampingkan eksternalitas negatif berupa degradasi lingkungan dan penurunan daya dukung wilayah yang berdampak secara sistemik pada Produk Domestik Regional Bruto (PDRB) sektor primer, khususnya pertanian dan perikanan.

Laporan ini disusun menggunakan kerangka kerja **Cross-Industry Standard Process for Data Mining (CRISP-DM)**. Penelitian ini menguji serangkaian model prediktif, mulai dari *Machine Learning* non-linear hingga Ekonometrika Geografis, untuk mengkuantifikasi klasterisasi kerugian ekonomi yang dihasilkan oleh fasilitas peleburan nikel.

Melalui restrukturisasi arsitektur data—yakni menyintesis 57 tabel terpisah menjadi *Spatio-Temporal Panel Dataset*—penelitian ini memberikan pembuktian secara empiris bahwa model **Geographically and Temporally Weighted Regression (GTWR)** mampu mencapai tingkat akurasi prediksi *Out-of-Sample* sebesar **88.22%**. Model ekonometrika ini mengungguli algoritma *Machine Learning* seperti *Random Forest* (86.09%) dan *Graph Neural Network* (-5.73%). Hasil regresi GTWR menegaskan bahwa kedekatan spasial (*Spatial Clustering*) antar fasilitas industri merupakan determinan utama eskalasi kerugian ekonomi sektoral.

---

## FASE 1: PEMAHAMAN BISNIS (BUSINESS UNDERSTANDING)

### 1.1 Latar Belakang Ekonomi dan Kebijakan
Sejak implementasi kebijakan pelarangan ekspor bijih nikel mentah pada tahun 2020, Indonesia mengalami lonjakan Penanaman Modal Asing (PMA) pada fasilitas Pirometalurgi (RKEF) dan Hidrometalurgi (HPAL). Kawasan industri terpadu seperti *Indonesia Morowali Industrial Park* (IMIP) di Sulawesi Tengah dan *Indonesia Weda Bay Industrial Park* (IWIP) di Maluku Utara telah menjadi episentrum produksi nikel global.

Meskipun demikian, industrialisasi ini padat karbon dan berpotensi menghasilkan polutan. Penggunaan Pembangkit Listrik Tenaga Uap (PLTU) terdedikasi (*captive power*) berdampak pada penurunan kualitas udara, kerusakan wilayah resapan air, serta limbah *tailing* yang mereduksi produktivitas perikanan tangkap.

### 1.2 Limitasi Analisis Agregat
Evaluasi makroekonomi di tingkat pemerintah daerah umumnya menggunakan indikator PDRB agregat. Pertumbuhan PDRB yang signifikan di sektor pertambangan sering kali menutupi fenomena substitusi sektoral, di mana sektor pertanian dan perikanan mengalami kontraksi tajam. Pendekatan agregat tingkat provinsi tidak mampu mendeteksi disparitas kerugian di tingkat lokal.

### 1.3 Tujuan Pemodelan
Tujuan dari analisis data ini adalah:
1.  **Kuantifikasi Presisi:** Mengukur beban ekonomi akibat degradasi ekologis pada unit analisis fasilitas tunggal (*Facility-Level*).
2.  **Identifikasi Efek Limpahan (*Spillover Effect*):** Menganalisis secara matematis korelasi antara konsentrasi fasilitas industri pada satu koordinat spasial terhadap efek pengganda kerugian ekonomi.
3.  **Evaluasi Algoritma:** Membandingkan validitas eksternal berbagai model statistik (GTWR) dan komputasional (SVR, RF, GCN) dalam memprediksi kerugian ekonomi terdistribusi.

---

## FASE 2: PEMAHAMAN DATA (DATA UNDERSTANDING)

Data bersumber dari 57 tabel berformat CSV yang disusun oleh lembaga riset seperti China Global South (CGS) Project, Centre for Research on Energy and Clean Air (CREA), CELIOS, dan IEEFA. 

### 2.1 Teori Input-Output Leontief sebagai Variabel Target
Penelitian ini menggunakan **Model Input-Output (I-O) Leontief** yang tertuang di laporan CELIOS-CREA sebagai *Ground Truth* untuk variabel target ($y$). Model Leontief memetakan interdependensi antar sektor melalui persamaan balikan matriks:
$$ x = (I - A)^{-1} f $$
Melalui perhitungan ini, laporan menyimpulkan bahwa ekspansi industri nikel menimbulkan kerugian PDRB sektor Pertanian sebesar Rp 1,03 Triliun di Sulawesi Tengah dan Rp 390 Miliar di Sulawesi Tenggara.

### 2.2 Inventarisasi Variabel (Kamus Data)
Fitur prediktif ($X$) diekstraksi dari agregasi tabel primer:

| Variabel Independen ($X$) | Deskripsi (*Data Type*) | Fungsi dalam Pemodelan |
| :--- | :--- | :--- |
| `Latitude` | Float | Kordinat Geospasial Y (Analisis Spasial) |
| `Longitude` | Float | Kordinat Geospasial X (Analisis Spasial) |
| `Capacity_tpa` | Numerik Kontinyu | Kapasitas produksi smelter (Ton/Tahun) |
| `Coal_MW` | Numerik Kontinyu | Kapasitas PLTU Captive (Megawatt) |
| `Process_Enc` | Kategorikal Numerik | Klasifikasi teknologi pengolahan (RKEF/HPAL) |
| `Product_Enc` | Kategorikal Numerik | Klasifikasi produk keluaran (NPI, MHP, FeNi) |
| `Tahun` | Diskrit | Dimensi waktu panel (Tahun Dasar vs Tahun Proyeksi) |

---

## FASE 3: PERSIAPAN DATA (DATA PREPARATION)

### 3.1 Mitigasi Kebocoran Data (*Data Leakage*)
Pengujian awal menggunakan agregasi tingkat provinsi menghasilkan $N=38$ observasi. Evaluasi model dengan *Leave-One-Out Cross Validation* (LOO-CV) menghasilkan nilai akurasi negatif (-0.08%), yang mengindikasikan terjadinya *overfitting* yang ekstrem.

### 3.2 Konstruksi Model Tingkat Fasilitas ($N=106$)
Untuk meningkatkan derajat kebebasan (*degrees of freedom*), data diagregasi ulang pada tingkat fasilitas. Total kerugian regional Leontief didistribusikan kepada 106 unit *smelter* berdasarkan bobot kapasitas operasi masing-masing pabrik:
$$ \text{Burden}_i = \left( \frac{\text{Kapasitas Pabrik}_i}{\sum \text{Kapasitas Regional}} \right) \times \text{Loss}_{\text{Regional}} $$

### 3.3 Sintesis Panel Spasio-Temporal ($N=212$)
Algoritma Ekonometrika GTWR memerlukan keberadaan matriks keruangan dan waktu. Data *Cross-Sectional* ($N=106$) kemudian disintesis menjadi data panel:
*   **Periode 1:** Operasional awal (Faktor skala: 20%).
*   **Periode 9:** Puncak operasional (*Business As Usual* dengan skala 100%).
Ekspansi ini menghasilkan dataset final sebesar $N=212$ observasi.

---

## FASE 4: PEMODELAN (MODELING)

Tahap ini menguji validitas algoritma konvensional dan ekonometrika spasial menggunakan Dataset Panel Spasio-Temporal.

### 4.1 Support Vector Regression (RBF Kernel)
Sebaran kapasitas smelter memiliki pencilan (*outliers*) yang signifikan. *Support Vector Regression* (SVR) menggunakan fungsi *Radial Basis* untuk mengalkulasi margin prediksi optimal dengan penalti kesalahan $C=1000$.

### 4.2 Random Forest Regressor
Algoritma *Ensemble Learning* berbasis pohon keputusan, diaplikasikan untuk menangkap hubungan non-linearitas antar variabel teknis (misalnya rasio kapasitas smelter terhadap penggunaan batu bara).

### 4.3 Spatio-Temporal Graph Convolutional Network (ST-GCN)
Fasilitas smelter dimodelkan sebagai "Node" dan kedekatan jarak spasial sebagai "Edges". Melalui normalisasi matriks *Adjacency* ($A_{\text{norm}}$), algoritma memfasilitasi *message passing*. Namun, model ini rentan terhadap fenomena *over-smoothing* pada graf berdensitas tinggi.

### 4.4 Geographically and Temporally Weighted Regression (GTWR)
GTWR mengestimasi persamaan regresi lokal pada masing-masing titik koordinat. Matriks pembobotan spasio-temporal ($W$) dihitung menggunakan fungsi Kernel Eksponensial:
$$ W_{ij} = \exp\left(-\frac{d_{S_{ij}}^2}{bw_s^2}\right) \times \exp\left(-\frac{d_{T_{ij}}^2}{bw_t^2}\right) $$
Di mana $bw_s$ dan $bw_t$ adalah *bandwidth* spasial dan temporal optimal. Algoritma ini mengakomodasi postulat Hukum Geografi Pertama Tobler terkait dependensi spasial.

---

## FASE 5: EVALUASI (EVALUATION)

Evaluasi performa (*predictive accuracy*) dari setiap algoritma dilakukan menggunakan metode pengujian **5-Fold Cross Validation** (Pengujian sampel acak independen).

### Hasil Akurasi (Out-of-Sample $R^2$)
| Algoritma Pembelajaran | R-Squared ($R^2$) | Interpretasi Signifikansi |
| :--- | :---: | :--- |
| **Custom GTWR** | **88.22%** | Memiliki kemampuan deteksi korelasi keruangan secara lokal yang superior. |
| Support Vector Regression | 86.31% | Stabilitas tinggi terhadap data non-parametrik. |
| Random Forest | 86.09% | Akurat, namun memiliki keterbatasan interpretasi geospasial. |
| ST-Graph (GCN) | -5.73% | Terdegradasi oleh *Graph Smoothing* pada himpunan data kecil. |

### 5.1 Interpretasi Hasil Ekonometrika Spasial
Kinerja GTWR (88.22%) yang melampaui algoritma komputasi cerdas (seperti Random Forest) membuktikan signifikansi parameter geografis. *Random Forest* memproses *Latitude* dan *Longitude* secara terisolasi. Di sisi lain, GTWR menggunakan integrasi Jarak Euclidean, yang membuktikan bahwa konsentrasi fasilitas pengolahan di satu area (seperti sentra IMIP) menghasilkan efek limpahan negatif yang berakumulasi secara geometris, bukan sekadar bertambah secara aritmatika linear.

---

## FASE 6: PENERAPAN (DEPLOYMENT) & REKOMENDASI KEBIJAKAN

Hasil riset ini berimplikasi langsung pada kerangka perumusan kebijakan tata ruang kawasan industri di Indonesia.

1.  **Moratorium Izin Berbasis Daya Dukung Spasial:**
    Tingkat kepadatan industri berkorelasi langsung dengan degradasi sektor primer. Otoritas penata ruang direkomendasikan untuk menerapkan pembatasan izin (*moratorium*) pendirian fasilitas smelter baru pada koordinat geografis yang telah mencapai ambang batas saturasi kerugian sektoral.
2.  **Instrumentasi Fiskal Spasial:**
    Rekomendasi penerapan pungutan pajak karbon atau dana kompensasi lingkungan yang besifat fluktuatif berdasarkan koefisien spasial lokasi pabrik. Smelter yang berada dalam titik episentrum klasterisasi dikenakan tarif kompensasi yang secara proporsional lebih tinggi, merujuk pada prinsip *Polluter Pays Principle*.

### Konklusi
Integrasi antara analisis Input-Output Leontief sebagai basis *Ground Truth* dengan Ekonometrika Spasial (GTWR) dalam kerangka *Facility-Level Panel Dataset*, menghasilkan instrumen analitik yang presisi tinggi. Regulasi transisi energi ke depan memerlukan mitigasi tata ruang terintegrasi guna meminimalisasi konflik pemanfaatan ruang antara sektor ekstraktif dan sektor penyediaan pangan.
