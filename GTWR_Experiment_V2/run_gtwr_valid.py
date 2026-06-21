import sys
import math
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Force UTF-8 output
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 1. LOAD DATA YANG VALID SECARA SPASIAL
MASTER = r"C:\Users\user\Downloads\IMIP\mastersheet_GTWR.csv"
print("[1] Membaca Data Valid (Tingkat Kabupaten)...")
df = pd.read_csv(MASTER, encoding='utf-8-sig')

# 2. FEATURE ENGINEERING (Mencegah Multikolinearitas & Data Leakage)
df_model = df.copy()
n = len(df_model)

# Normalisasi Waktu
yr_min, yr_max = df_model['Year'].min(), df_model['Year'].max()
df_model['Year_norm'] = (df_model['Year'] - yr_min) / (yr_max - yr_min + 1e-10)

# Koordinat Spasial yang Valid (12 Titik Berbeda)
df_model['Lat_norm'] = (df_model['Latitude'] - df_model['Latitude'].mean()) / (df_model['Latitude'].std() + 1e-10)
df_model['Lon_norm'] = (df_model['Longitude'] - df_model['Longitude'].mean()) / (df_model['Longitude'].std() + 1e-10)

# Fitur Prediktor yang dipilih (Menghindari fitur berlebihan/overfitting)
X_cols = ['CO2_Mt', 'Coal_MW', 'Emission_Intensity']
Y_col  = 'PDRB_BAU_TrRp'

X_raw  = df_model[X_cols].fillna(0).values
y      = df_model[Y_col].fillna(0).values

# Standardize X
X_mean, X_std = X_raw.mean(axis=0), X_raw.std(axis=0) + 1e-10
X_norm = (X_raw - X_mean) / X_std
X_norm = np.column_stack([np.ones(n), X_norm]) # Intercept

coords_s = df_model[['Lat_norm','Lon_norm']].values
coords_t = df_model['Year_norm'].values

# 3. KERNEL & LEAVE-ONE-OUT CROSS VALIDATION (LOO-CV)
# LOO-CV adalah kunci menghindari Data Leakage In-Sample
def gauss(d, bw):
    return np.exp(-0.5 * (d / (bw + 1e-10))**2)

def gtwr_loo(bw_s, bw_t):
    y_pred_cv = np.zeros(n)
    for i in range(n):
        d_s = np.sqrt(np.sum((coords_s - coords_s[i])**2, axis=1))
        d_t = np.abs(coords_t - coords_t[i])
        w = gauss(d_s, bw_s) * gauss(d_t, bw_t)
        
        # HAPUS observasi i dari penentuan bobot (Mencegah Model Menyontek Jawaban Sendiri!)
        w[i] = 0.0 
        
        if w.sum() < 1e-10:
            y_pred_cv[i] = y.mean()
            continue
            
        W = np.diag(w)
        Xw = X_norm.T @ W @ X_norm
        try:
            beta = np.linalg.solve(Xw + np.eye(Xw.shape[0]) * 1e-5, X_norm.T @ W @ y)
            y_pred_cv[i] = X_norm[i] @ beta
        except np.linalg.LinAlgError:
            y_pred_cv[i] = y.mean()
            
    # Hitung Out-Of-Sample R-Squared yang JUJUR
    ss_res_cv = np.sum((y - y_pred_cv)**2)
    ss_tot = np.sum((y - y.mean())**2)
    r2_cv = 1.0 - ss_res_cv / (ss_tot + 1e-10)
    return r2_cv, y_pred_cv

# 4. GRID SEARCH (Mencari Bandwidth Tanpa Overfitting)
print("[2] Menjalankan Cross-Validation (Mencari R2 Jujur/Out-Of-Sample)...")
best_r2_cv = -float('inf')
best_bw_s, best_bw_t = 1.0, 0.5

# Pilihan bandwidth (resolusi)
for bw_s in [0.5, 1.0, 1.5, 2.0]:
    for bw_t in [0.3, 0.5, 0.8]:
        r2_cv, _ = gtwr_loo(bw_s, bw_t)
        marker = " <-- Tahan Banting!" if r2_cv > best_r2_cv else ""
        print(f"    BW_Spatial={bw_s:.1f}, BW_Temporal={bw_t:.1f}  -> Out-of-Sample R2: {r2_cv:7.4f}{marker}")
        if r2_cv > best_r2_cv:
            best_r2_cv = r2_cv
            best_bw_s, best_bw_t = bw_s, bw_t

# 5. HASIL AKHIR & INTERPRETASI
_, y_pred_final = gtwr_loo(best_bw_s, best_bw_t)
rmse_cv = math.sqrt(np.mean((y - y_pred_final)**2))

print("\n=======================================================")
print("  AUDIT HASIL GTWR (ANTI-DATA LEAKAGE)")
print("=======================================================")
print(f"  Total Observasi  : {n} (12 Kabupaten, Titik Koordinat Unik)")
print(f"  Target Variabel  : {Y_col}")
print(f"  Model Terbaik    : BW Spasial = {best_bw_s}, BW Temporal = {best_bw_t}")
print(f"  R-Squared Jujur  : {best_r2_cv:.4f} (Valid Out-of-Sample)")
print(f"  RMSE CV          : {rmse_cv:.4f} Triliun Rp")
print("=======================================================")

if best_r2_cv > 0.3:
    print("\nKESIMPULAN: Model INI VALID SECARA AKADEMIS! ✅")
    print(f"Meski tanpa membocorkan data (Data Leakage dihentikan),")
    print(f"model spasio-temporal masih mampu menjelaskan {best_r2_cv*100:.1f}% fenomena ekonomi.")
    print("Inilah angka akurasi yang sesungguhnya layak dimasukkan ke dalam skripsi/jurnal.")
else:
    print("\nKESIMPULAN: MODEL GAGAL UJI VALIDASI ❌")
    print("Ketika kebocoran data ditutup, model kehilangan daya prediksinya.")
    print("Artinya hasil 92% sebelumnya murni ilusi overfitting.")
