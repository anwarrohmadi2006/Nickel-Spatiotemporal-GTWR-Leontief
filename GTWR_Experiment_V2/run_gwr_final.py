import sys
import math
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 1. LOAD DATA RESOLUSI KABUPATEN
MASTER = r"C:\Users\user\Downloads\IMIP\mastersheet_GTWR.csv"
print("[1] Membaca Data Mastersheet Kabupaten...")
df_all = pd.read_csv(MASTER, encoding='utf-8-sig')

# 2. DATA PREPARATION: Ganti menjadi "First-Difference Model"
# Mengatasi Bias Resolusi Temporal dengan membandingkan Tahun 2029 (Tahun 9) vs 2020 (Tahun 1)
df_2020 = df_all[df_all['Year'] == 2020].set_index('Regency')
df_2029 = df_all[df_all['Year'] == 2029].set_index('Regency')

# Pastikan hanya regency yang ada di kedua tahun
common_regencies = df_2020.index.intersection(df_2029.index)
df_2020 = df_2020.loc[common_regencies]
df_2029 = df_2029.loc[common_regencies]

df_gwr = pd.DataFrame(index=common_regencies)
df_gwr['Province'] = df_2020['Province']
df_gwr['Latitude'] = df_2020['Latitude']
df_gwr['Longitude'] = df_2020['Longitude']

# Target: Delta PDRB (Tahun 2029 dikurangi Tahun 2020)
df_gwr['Delta_PDRB_TrRp'] = df_2029['PDRB_BAU_TrRp'] - df_2020['PDRB_BAU_TrRp']

# Fitur (Agregat Emisi/Kapasitas pada tahun tersebut)
df_gwr['Avg_CO2_Mt'] = (df_2020['CO2_Mt'] + df_2029['CO2_Mt']) / 2.0
df_gwr['Coal_MW'] = df_2029['Coal_MW']
df_gwr['N_Smelters'] = df_2029['N_Smelters']

n = len(df_gwr)
print(f"    Berhasil memproses {n} Kabupaten (Resolusi Spasial Tinggi)")

# 3. NORMALISASI KOORDINAT & FITUR
df_gwr['Lat_norm'] = (df_gwr['Latitude'] - df_gwr['Latitude'].mean()) / (df_gwr['Latitude'].std() + 1e-10)
df_gwr['Lon_norm'] = (df_gwr['Longitude'] - df_gwr['Longitude'].mean()) / (df_gwr['Longitude'].std() + 1e-10)

X_cols = ['Avg_CO2_Mt', 'Coal_MW', 'N_Smelters']
X_raw = df_gwr[X_cols].values
X_norm = (X_raw - X_raw.mean(axis=0)) / (X_raw.std(axis=0) + 1e-10)
X_norm = np.column_stack([np.ones(n), X_norm])

y = df_gwr['Delta_PDRB_TrRp'].values
coords_s = df_gwr[['Lat_norm', 'Lon_norm']].values

# 4. ALGORITMA GWR (Spasial Saja) DENGAN LOO-CV
def gauss(d, bw):
    return np.exp(-0.5 * (d / (bw + 1e-10))**2)

def gwr_loo(bw_s):
    y_pred_cv = np.zeros(n)
    for i in range(n):
        d_s = np.sqrt(np.sum((coords_s - coords_s[i])**2, axis=1))
        w = gauss(d_s, bw_s)
        
        # Cegah Data Leakage (LOO)
        w[i] = 0.0
        
        if w.sum() < 1e-10:
            y_pred_cv[i] = y.mean()
            continue
            
        W = np.diag(w)
        Xw = X_norm.T @ W @ X_norm
        try:
            beta = np.linalg.solve(Xw + np.eye(Xw.shape[0]) * 1e-4, X_norm.T @ W @ y)
            y_pred_cv[i] = X_norm[i] @ beta
        except np.linalg.LinAlgError:
            y_pred_cv[i] = y.mean()
            
    ss_res_cv = np.sum((y - y_pred_cv)**2)
    ss_tot = np.sum((y - y.mean())**2)
    r2_cv = 1.0 - ss_res_cv / (ss_tot + 1e-10)
    return r2_cv, y_pred_cv

print("\n[2] Mencari Bandwidth Spasial Optimal (LOO-CV)...")
best_r2_cv = -float('inf')
best_bw_s = 1.0

for bw_s in [0.5, 0.8, 1.0, 1.5, 2.0, 3.0, 5.0]:
    r2_cv, _ = gwr_loo(bw_s)
    marker = " <-- Paling Optimal" if r2_cv > best_r2_cv else ""
    print(f"    BW_Spatial={bw_s:.1f} -> Out-of-Sample R2: {r2_cv:7.4f}{marker}")
    if r2_cv > best_r2_cv:
        best_r2_cv = r2_cv
        best_bw_s = bw_s

# 5. EKSEKUSI MODEL FINAL (In-Sample untuk koefisien, Out-of-sample untuk Validitas)
y_hat_final, resid_final, betas_final = [], [], []

for i in range(n):
    d_s = np.sqrt(np.sum((coords_s - coords_s[i])**2, axis=1))
    w = gauss(d_s, best_bw_s)
    W = np.diag(w)
    
    Xw = X_norm.T @ W @ X_norm
    try:
        beta = np.linalg.solve(Xw + np.eye(Xw.shape[0])*1e-4, X_norm.T @ W @ y)
    except:
        beta = np.zeros(X_norm.shape[1])
        
    yhat = float(X_norm[i] @ beta)
    y_hat_final.append(yhat)
    resid_final.append(y[i] - yhat)
    betas_final.append(beta)

y_arr = np.array(y)
resid_arr = np.array(resid_final)
ss_res = np.sum(resid_arr**2)
ss_tot = np.sum((y_arr - y_arr.mean())**2)
r2_insample = 1 - (ss_res / (ss_tot + 1e-10))

print("\n=======================================================")
print("  HASIL FINAL GWR (GEOGRAPHICALLY WEIGHTED REGRESSION)")
print("=======================================================")
print(f"  Target         : Delta PDRB (2029 - 2020)")
print(f"  Total Observasi: {n} Kabupaten")
print(f"  BW Spasial     : {best_bw_s}")
print(f"  R2 Out-of-Sample : {best_r2_cv:.4f} (Akurasi Prediktif Jujur)")
print(f"  R2 In-Sample     : {r2_insample:.4f} (Akurasi Eksplanatori)")
print("=======================================================")

betas_arr = np.array(betas_final)
print(f"\nRata-rata Koefisien (Standarisasi):")
print(f"  Intercept      : {betas_arr[:,0].mean():>8.4f}")
print(f"  Avg_CO2_Mt     : {betas_arr[:,1].mean():>8.4f} (Dampak Emisi thd Kerugian Ekonomi)")
print(f"  Coal_MW        : {betas_arr[:,2].mean():>8.4f} (Dampak Ekspansi PLTU)")
print(f"  N_Smelters     : {betas_arr[:,3].mean():>8.4f} (Efek Aglomerasi Pabrik)")

df_gwr['Delta_PDRB_Pred'] = np.round(y_hat_final, 3)
df_gwr['Residual'] = np.round(resid_arr, 3)
for i, col in enumerate(['Intercept'] + X_cols):
    df_gwr[f'Beta_{col}'] = np.round(betas_arr[:, i], 4)

import os
out_path = os.path.join(os.getcwd(), "GWR_Final_Valid_Results.csv")
df_gwr.to_csv(out_path)
print(f"\n[DONE] Data prediksi & spasial beta diekspor ke: {out_path}")
