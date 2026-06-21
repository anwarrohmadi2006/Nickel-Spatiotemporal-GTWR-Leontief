import numpy as np
import pandas as pd
import math
import os

# 1. BUAT DATASET SINTETIS 68 BARIS (Berdasarkan 17 Sektor × 2 Provinsi × 2 Periode)
# Meniru "GTWR v2 Target Independen" dari eksperimen sebelumnya
sektor_list = [
    "Pertanian", "Pertambangan", "Industri Pengolahan", "Listrik & Gas",
    "Pengadaan Air", "Konstruksi", "Perdagangan", "Transportasi",
    "Penyediaan Akomodasi", "Info & Komunikasi", "Jasa Keuangan",
    "Real Estat", "Jasa Perusahaan", "Admin Pemerintahan",
    "Jasa Pendidikan", "Jasa Kesehatan", "Jasa Lainnya"
]

data = []
prov_coords = {
    "Sulteng": (-1.4300, 121.4456), # Latitude, Longitude (estimasi centroid)
    "Sultra":  (-4.1449, 122.1746)
}

# Simulasi Dampak Ekonomi BAU (Triliun Rp)
# Pola: Tahun 1 (Konstruksi) dominan positif, Tahun 9 (Operasi kotor) hancur (terutama Pertanian)
for prov, (lat, lon) in prov_coords.items():
    for waktu in [1, 9]: # Tahun 1 dan Tahun 9
        for sektor in sektor_list:
            
            # Feature engineering dasar
            is_agri = 1 if sektor == "Pertanian" else 0
            is_mine = 1 if sektor == "Pertambangan" else 0
            
            # Simulasi Y (PDRB Sektoral) berdasarkan pola CREA
            if waktu == 1:
                y_pdrb = np.random.uniform(0.1, 5.0) # Mayoritas positif saat konstruksi
                if is_mine: y_pdrb += 10.0
            else:
                y_pdrb = np.random.uniform(-1.0, 1.0) # Mulai negatif saat operasi
                if is_agri: y_pdrb -= np.random.uniform(5.0, 15.0) # Hancur karena polusi
                
            data.append({
                "Provinsi": prov,
                "Sektor": sektor,
                "Tahun_Operasi": waktu,
                "Latitude": lat,
                "Longitude": lon,
                "Is_Agri": is_agri,
                "Is_Mine": is_mine,
                "PDRB_BAU_TrRp": round(y_pdrb, 3)
            })

df = pd.DataFrame(data)
print(f"Data Shape: {df.shape}") # Harus 68 rows (17x2x2)

# 2. IMPLEMENTASI GTWR v2
def gauss(d, bw):
    return np.exp(-0.5 * (d / (bw + 1e-10))**2)

n = len(df)
coords_s = df[['Latitude', 'Longitude']].values
coords_t = df['Tahun_Operasi'].values

# Standardize X
X_cols = ['Is_Agri', 'Is_Mine']
X_raw = df[X_cols].values
X_norm = (X_raw - X_raw.mean(axis=0)) / (X_raw.std(axis=0) + 1e-10)
X_norm = np.column_stack([np.ones(n), X_norm]) # Intercept

y = df['PDRB_BAU_TrRp'].values

# Gunakan bandwidth yang direkomendasikan di Brainstorm.md
best_bw_s = 2.0
best_bw_t = 0.7  # tau

print("\n--- MENJALANKAN MODEL GTWR V2 ---")
print(f"Observasi         : {n}")
print(f"Bandwidth Spasial : {best_bw_s}")
print(f"Bandwidth Temporal: {best_bw_t}")

y_hat_all = []
resid_all = []
betas_all = []

for i in range(n):
    # Hitung Jarak Spasio-Temporal
    d_s = np.sqrt(np.sum((coords_s - coords_s[i])**2, axis=1))
    d_t = np.abs(coords_t - coords_t[i])
    
    # Kernel Pembobot
    w = gauss(d_s, best_bw_s) * gauss(d_t, best_bw_t)
    W = np.diag(w)
    
    # Weighted Least Squares
    Xw = X_norm.T @ W @ X_norm
    beta = np.linalg.solve(Xw + np.eye(Xw.shape[0])*1e-6, X_norm.T @ W @ y)
    
    yhat = float(X_norm[i] @ beta)
    y_hat_all.append(yhat)
    resid_all.append(y[i] - yhat)
    betas_all.append(beta)

y_arr = np.array(y)
yhat_arr = np.array(y_hat_all)
resid_arr = np.array(resid_all)

# Hitung R-Squared
ss_res = np.sum(resid_arr**2)
ss_tot = np.sum((y_arr - y_arr.mean())**2)
R2 = 1 - (ss_res / ss_tot)
RMSE = np.sqrt(np.mean(resid_arr**2))

print("\n--- HASIL GTWR V2 ---")
print(f"Global R-Squared : {R2:.4f}")
print(f"RMSE             : {RMSE:.4f} Triliun Rp")

betas_arr = np.array(betas_all)
print(f"\nRata-rata Koefisien (Beta):")
print(f"  Intercept    : {betas_arr[:,0].mean():.4f} (Baseline Ekonomi)")
print(f"  Is_Agri      : {betas_arr[:,1].mean():.4f} (Dampak ke Pertanian)")
print(f"  Is_Mine      : {betas_arr[:,2].mean():.4f} (Dampak ke Pertambangan)")

# Simpan hasil
out_path = os.path.join(os.getcwd(), "GTWR_V2_Results.csv")
df['Prediksi_PDRB'] = yhat_arr
df['Residual'] = resid_arr
df.to_csv(out_path, index=False)
print(f"\nEksperimen selesai. Hasil disimpan di: {out_path}")
