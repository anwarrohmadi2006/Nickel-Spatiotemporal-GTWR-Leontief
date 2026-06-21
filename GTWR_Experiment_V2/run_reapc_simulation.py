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
df_2020 = df_all[df_all['Year'] == 2020].set_index('Regency')
df_2029 = df_all[df_all['Year'] == 2029].set_index('Regency')

common_regencies = df_2020.index.intersection(df_2029.index)
df_2020 = df_2020.loc[common_regencies]
df_2029 = df_2029.loc[common_regencies]

df_gwr = pd.DataFrame(index=common_regencies)
df_gwr['Province'] = df_2020['Province']
df_gwr['Latitude'] = df_2020['Latitude']
df_gwr['Longitude'] = df_2020['Longitude']

# Target: Delta PDRB (Kerugian/Beban Ekonomi Triliun Rp)
df_gwr['Delta_PDRB_TrRp'] = df_2029['PDRB_BAU_TrRp'] - df_2020['PDRB_BAU_TrRp']

# Fitur BAU
df_gwr['Avg_CO2_Mt'] = (df_2020['CO2_Mt'] + df_2029['CO2_Mt']) / 2.0
df_gwr['Coal_MW'] = df_2029['Coal_MW']
df_gwr['N_Smelters'] = df_2029['N_Smelters']

n = len(df_gwr)

# 3. NORMALISASI KOORDINAT & FITUR BAU
df_gwr['Lat_norm'] = (df_gwr['Latitude'] - df_gwr['Latitude'].mean()) / (df_gwr['Latitude'].std() + 1e-10)
df_gwr['Lon_norm'] = (df_gwr['Longitude'] - df_gwr['Longitude'].mean()) / (df_gwr['Longitude'].std() + 1e-10)

X_cols = ['Avg_CO2_Mt', 'Coal_MW', 'N_Smelters']
X_raw_BAU = df_gwr[X_cols].values

# Simpan Mean dan Std dari BAU untuk menstandarkan Skenario RE+APC nantinya
mean_BAU = X_raw_BAU.mean(axis=0)
std_BAU = X_raw_BAU.std(axis=0) + 1e-10

X_norm_BAU = (X_raw_BAU - mean_BAU) / std_BAU
X_norm_BAU = np.column_stack([np.ones(n), X_norm_BAU]) # Add Intercept

y = df_gwr['Delta_PDRB_TrRp'].values
coords_s = df_gwr[['Lat_norm', 'Lon_norm']].values

# 4. ALGORITMA GWR: FUNGSI GAUSS DAN MODELING
def gauss(d, bw):
    return np.exp(-0.5 * (d / (bw + 1e-10))**2)

best_bw_s = 0.8 # Hasil optimasi sebelumnya (run_gwr_final.py)

print("\n[2] Menjalankan Model GWR Baseline (Skenario BAU)...")
betas_final = []
yhat_BAU = []

for i in range(n):
    d_s = np.sqrt(np.sum((coords_s - coords_s[i])**2, axis=1))
    w = gauss(d_s, best_bw_s)
    W = np.diag(w)
    
    Xw = X_norm_BAU.T @ W @ X_norm_BAU
    try:
        beta = np.linalg.solve(Xw + np.eye(Xw.shape[0])*1e-4, X_norm_BAU.T @ W @ y)
    except:
        beta = np.zeros(X_norm_BAU.shape[1])
        
    yhat = float(X_norm_BAU[i] @ beta)
    yhat_BAU.append(yhat)
    betas_final.append(beta)

# 5. SIMULASI SKENARIO RE+APC (COUNTER-FACTUAL)
print("\n[3] Menginjeksi Skenario Transisi RE+APC (Reduksi Polutan 80%)...")
# Modifikasi Data Asli (Sebelum Normalisasi)
X_raw_REAPC = X_raw_BAU.copy()

# Index kolom: 0=Avg_CO2_Mt, 1=Coal_MW, 2=N_Smelters
# Asumsi: Transisi energi memangkas emisi dan penggunaan PLTU sebesar 80% (menyisakan 20%)
X_raw_REAPC[:, 0] = X_raw_REAPC[:, 0] * 0.2  
X_raw_REAPC[:, 1] = X_raw_REAPC[:, 1] * 0.2  
# Jumlah pabrik (N_Smelters) tetap 100% (Ekspansi industri berlanjut namun hijau)

# Normalisasi X_REAPC MENGGUNAKAN PARAMETER BAU (Mean & Std BAU) agar ekuivalen
X_norm_REAPC = (X_raw_REAPC - mean_BAU) / std_BAU
X_norm_REAPC = np.column_stack([np.ones(n), X_norm_REAPC])

yhat_REAPC = []
for i in range(n):
    # Gunakan Koefisien Beta yang sama dari model BAU (karena elastisitas struktural wilayah tetap)
    y_reapc_pred = float(X_norm_REAPC[i] @ betas_final[i])
    yhat_REAPC.append(y_reapc_pred)

yhat_BAU_arr = np.array(yhat_BAU)
yhat_REAPC_arr = np.array(yhat_REAPC)

# Surplus PDRB = Kerugian BAU - Kerugian RE+APC (Jika Delta PDRB bernilai negatif/kerugian)
surplus_arr = yhat_BAU_arr - yhat_REAPC_arr
total_surplus_TrRp = np.sum(surplus_arr)

print("\n===========================================================")
print("     HASIL SIMULASI KOMPUTASI GWR (BAU vs RE+APC)          ")
print("===========================================================")
print(f"Total Kerugian PDRB Skenario BAU     : Rp {np.sum(yhat_BAU_arr):.2f} Triliun")
print(f"Total Kerugian PDRB Skenario RE+APC  : Rp {np.sum(yhat_REAPC_arr):.2f} Triliun")
print("-----------------------------------------------------------")
if total_surplus_TrRp > 0:
    print(f"SURPLUS PDRB YANG DISELAMATKAN       : Rp {total_surplus_TrRp:.2f} Triliun (Vektor Positif)")
else:
    print(f"SURPLUS PDRB YANG DISELAMATKAN       : Rp {total_surplus_TrRp:.2f} Triliun (Vektor Negatif)")
print("===========================================================")

# Export Hasil Simulasi
df_sim = pd.DataFrame(index=df_gwr.index)
df_sim['Province'] = df_gwr['Province']
df_sim['Kerugian_BAU_TrRp'] = np.round(yhat_BAU_arr, 3)
df_sim['Kerugian_REAPC_TrRp'] = np.round(yhat_REAPC_arr, 3)
df_sim['Surplus_Diselamatkan_TrRp'] = np.round(surplus_arr, 3)

out_sim = r"C:\Users\user\Downloads\IMIP\RE_APC_Simulation_Results.csv"
df_sim.to_csv(out_sim)
print(f"\n[DONE] Matriks hasil simulasi counter-factual disimpan ke: {out_sim}")
