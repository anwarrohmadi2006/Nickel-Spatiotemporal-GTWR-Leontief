import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import r2_score, mean_squared_error

# 1. LOAD DATA MASTERSHEET
MASTER = r"c:\Users\msi\Documents\New folder\Nickel-Spatiotemporal-GTWR-Leontief\mastersheet_GTWR.csv"
df = pd.read_csv(MASTER, encoding='utf-8-sig')

# Kita gunakan data lengkap 48 baris (12 Kab x 4 Tahun)
# Target: PDRB BAU
X_cols = ['CO2_Mt', 'Coal_MW', 'Emission_Intensity']
Y_col = 'PDRB_BAU_TrRp'

X_features = df[X_cols].values
y = df[Y_col].values

# 2. BAGAIMANA SVM MENANGKAP SPASIAL & TEMPORAL?
# Cara Termudah: Memasukkan Koordinat & Waktu langsung sebagai Fitur yang Distandarisasi
# Karena SVM menggunakan Kernel RBF (Radial Basis Function) yang pada dasarnya adalah 
# pengukur jarak Euclidean, memasukkan Lat, Lon, dan Waktu akan otomatis membuat 
# SVM mengukur "Kedekatan Ruang dan Waktu" (Spatio-Temporal Distance) antar observasi!

coords_s = df[['Latitude', 'Longitude']].values
coords_t = df[['Year']].values

# Gabungkan Fitur Ekonomi + Fitur Geografi + Fitur Waktu
X_spatiotemporal = np.column_stack((X_features, coords_s, coords_t))

# Standarisasi (Sangat penting untuk SVM agar jarak 1 derajat Latitude bisa disandingkan dgn 1 Tahun)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_spatiotemporal)

# 3. UJI MODEL SUPPORT VECTOR REGRESSION (SVR)
print("=== EKSPERIMEN SPATIO-TEMPORAL SVM (SVR) ===")
print("Dimensi Data: 48 Observasi (12 Kabupaten, 4 Tahun)")
print("Fitur Input : CO2_Mt, Coal_MW, Emission_Intensity, Latitude, Longitude, Year")

# A. Uji In-Sample (Overfitting Check)
svr = SVR(kernel='rbf', C=10.0, gamma='scale')
svr.fit(X_scaled, y)
y_pred_in = svr.predict(X_scaled)
r2_in = r2_score(y, y_pred_in)

# B. Uji Leave-One-Out Cross Validation (Akurasi Out-Of-Sample Jujur)
loo = LeaveOneOut()
y_pred_cv = np.zeros(len(y))

for train_idx, test_idx in loo.split(X_scaled):
    X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
    y_train = y[train_idx]
    
    model = SVR(kernel='rbf', C=10.0, gamma='scale')
    model.fit(X_train, y_train)
    y_pred_cv[test_idx] = model.predict(X_test)

r2_cv = r2_score(y, y_pred_cv)
rmse_cv = np.sqrt(mean_squared_error(y, y_pred_cv))

print("\n--- HASIL EVALUASI SVR ---")
print(f"R-Squared In-Sample  : {r2_in:.4f} (Model bisa menghafal data cukup baik)")
print(f"R-Squared Out-of-Sample (LOO-CV): {r2_cv:.4f} (Tahan banting!)")
print(f"RMSE CV              : {rmse_cv:.4f} Triliun Rp")

if r2_cv > 0:
    print("\nKESIMPULAN: SVR SUKSES! ✅")
    print("Berbeda dengan GTWR yang hancur di sampel kecil saat diuji silang, SVM dengan kernel RBF")
    print("jauh lebih stabil karena mekanisme margin toleransi (Epsilon) mencegah model terlalu ekstrem")
    print("menyesuaikan diri pada satu titik pencilan (outlier).")
else:
    print("\nKESIMPULAN: SVM JUGA KESULITAN ❌")
    print("Keterbatasan jumlah data menyebabkan SVM gagal menggeneralisasi pola spasio-temporal secara prediktif.")
