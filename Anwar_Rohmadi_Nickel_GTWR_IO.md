# Evaluasi Spasio-Temporal Kerugian Ekonomi Lintas Sektor Akibat Ekspansi Industri Nikel: Integrasi Model Input-Output Leontief dan GTWR
*Oleh: Anwar Rohmadi*

## 1. Pendahuluan
Transisi energi global menuju kendaraan listrik (*Electric Vehicles*) telah memicu lonjakan eksponensial dalam permintaan nikel. Indonesia, sebagai pemilik cadangan nikel terbesar di dunia, merespons ini dengan ekspansi masif fasilitas *smelter* di kawasan timur Indonesia, khususnya Sulawesi Tengah, Sulawesi Tenggara, dan Maluku Utara. Namun, industrialisasi hilirisasi ini sering kali mengabaikan *trade-off* lintas sektor. Laporan CREA dan CELIOS menunjukkan bahwa ledakan sektor pertambangan dan pengolahan nikel berdampak langsung pada pelemahan daya dukung lingkungan yang berimbas pada kerugian masif di sektor primer (pertanian dan perikanan) serta kesehatan publik. Penelitian ini bertujuan memodelkan dan mengkuantifikasi klasterisasi kerugian ekonomi tersebut menggunakan pendekatan ekonometrika spasial mutakhir.

## 2. Metodologi: Pendekatan Input-Output Leontief sebagai "Pabrik Data" (*Ground Truth*)
Penelitian ini memisahkan secara tegas antara **Ilmu Ekonomi (Leontief)** dan **Ilmu Spasial (GTWR)**. 
Untuk menghindari bias estimasi dalam mendefinisikan "Beban Kerugian Ekonomi", penelitian ini tidak menerka-nerka angka kerugian, melainkan menggunakan hasil hitungan **Model Input-Output (I-O) Leontief** dari laporan CREA/CELIOS sebagai dasar pijakan mutlak (*Ground Truth*). 

Teori pemenang Nobel ini memetakan interdependensi antar sektor melalui persamaan matriks:

$$ x = (I - A)^{-1} f $$

Melalui Matriks Balikan Leontief (*Leontief Inverse Matrix*), model membuktikan secara matematis bahwa aliran investasi dan guncangan (*shock*) skenario BAU ke Sektor Ekstraktif secara struktural "merampas" daya dukung Sektor Primer. 

**Hasil dari Model Leontief** berhasil mengkuantifikasi bahwa ekspansi industri nikel memicu total kerugian Produk Domestik Regional Bruto (PDRB) sektor Pertanian hingga mencapai **Rp 1,03 Triliun (Sulawesi Tengah)** dan **Rp 390 Miliar (Sulawesi Tenggara)**. 

Angka kerugian raksasa hasil perhitungan matematis Leontief inilah yang kemudian ditarik, didistribusikan secara proporsional ke 106 fasilitas *smelter*, dan dijadikan sebagai variabel target empiris (*Target Variable*) untuk diprediksi klasterisasi spasialnya oleh algoritma GTWR pada tahap selanjutnya.

## 3. Desain Arsitektur Data (*Facility-Level Modeling*)
Tantangan terbesar dalam ekonometrika spasial di Indonesia adalah kutukan sampel kecil (*small sample curse*). Agregasi data pada tingkat Provinsi atau Kabupaten kerap kali menghasilkan ilusi statistik (*Data Leakage*) di mana model mengalami *overfitting* yang ekstrem (In-Sample $R^2$ > 0.90, namun Out-of-Sample $R^2$ < 0).

Untuk membongkar kebuntuan ini, penelitian ini melakukan perombakan arsitektur besar-besaran menjadi **Facility-Level Modeling**. Sebanyak 57 tabel terpisah dari CGS, CREA, dan IEEFA direkonstruksi menjadi **106 Fasilitas Smelter Individu**. Beban kerugian ekonomi Leontief didistribusikan ke setiap pabrik menggunakan bobot kapasitas (*Capacity TPA*) dan letak geografis (*Latitude/Longitude*). Data ini kemudian disintesis menjadi **Data Panel Spasio-Temporal (N=212)** yang membandingkan kondisi "Tahun 1" (Awal Operasi) dan "Tahun 9" (Puncak Ekspansi BAU).

## 4. *The Ultimate Model Showdown*: Hasil dan Pembahasan
Empat arsitektur algoritma diuji tarungkan di atas arena **5-Fold Cross Validation** untuk mengukur tingkat akurasi riil (*Out-of-Sample*) dari masing-masing model dalam memprediksi kerugian ekonomi yang ditimbulkan suatu fasilitas *smelter*.

| Algoritma / Model | R-Squared (Out-of-Sample) | Keterangan Karakteristik |
| :--- | :--- | :--- |
| **Random Forest** | 86.09% | Model non-linear berbasis *Decision Tree*, sangat kuat membaca kapasitas produksi, namun lemah melihat geometri keruangan. |
| **SVR (RBF Kernel)** | 86.31% | *Support Vector* menangani pencilan (*outliers*) raksasa (kapasitas IMIP/IWIP) dengan margin yang stabil. |
| **Spatio-Temporal Graph (GCN)** | -5.73% | Algoritma *Graph Convolution* terlalu canggih sehingga meleburkan varians data (*Graph Smoothing*) pada ukuran N=212. |
| **Custom GTWR** | **88.22%** | Memadukan bobot geografis (Euclidean) dan waktu (Temporal). Pemenang mutlak! |

### Mengapa GTWR Mendominasi?
Kemenangan **Geographically and Temporally Weighted Regression (GTWR)** dengan skor **88.22%** bukanlah sebuah kebetulan matematis, melainkan pembuktian dari **Hukum Geografi Pertama Tobler**: *"Segala sesuatu saling berhubungan, namun sesuatu yang berdekatan memiliki hubungan yang lebih erat"*.

Tidak seperti Random Forest yang memandang *Latitude* dan *Longitude* sekadar sebagai "angka numerik biasa", GTWR menggunakan Kernel Eksponensial untuk menghitung matriks invers jarak spasial. GTWR secara eksplisit menyadari bahwa jika ada sepuluh *smelter* raksasa yang berdiri berhimpitan di dalam satu kawasan industri (seperti IMIP di Morowali), debu batu bara dan limbah polusi cair (*tailing*) yang mereka hasilkan akan membentuk efek *spillover* spasial yang melipatgandakan kerugian hasil panen pada koordinat yang sama secara eksponensial.

## 5. Kesimpulan
Pendekatan ekonometrika spasial mutakhir membuktikan bahwa daya rusak ekonomi dan lingkungan dari industri nikel tidak hanya ditentukan oleh spesifikasi pabrik semata (misal: RKEF vs HPAL, atau jumlah MW PLTU *captive*). **Zonasi Geografis (Klasterisasi Kawasan)** memegang peranan vital yang sangat merusak. Kebijakan pemusatan ratusan pabrik ekstraktif di satu koordinat pesisir (seperti di Sulawesi dan Maluku) secara matematis menciptakan "zona kematian ekologis" yang melumpuhkan utilitas ekonomi lintas sektor (Teori Leontief). Oleh karena itu, skenario dekarbonisasi dan Transisi Energi (RE+APC) harus memasukkan mitigasi spasial sebagai variabel utama, bukan sekadar memensiunkan batu bara.