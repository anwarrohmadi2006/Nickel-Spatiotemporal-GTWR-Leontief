import numpy as np
import pandas as pd
import glob
import os

# 1. LOAD DATA ASLI DARI CSV CREA-CELIOS
print("[1] Membaca data sektoral asli...")

csv_dir = r"c:\Users\msi\Documents\New folder\Nickel-Spatiotemporal-GTWR-Leontief\tables_csv"

# Mapping file ke (Provinsi, Tahun)
file_map = {
    "Table06": ("Sulteng", 1),
    "Table08": ("Sulteng", 9),
    "Table10": ("Sultra", 1),
    "Table12": ("Sultra", 9)
}

prov_coords = {
    "Sulteng": (-1.4300, 121.4456),
    "Sultra":  (-4.1449, 122.1746)
}

all_files = glob.glob(os.path.join(csv_dir, "CREA_CELIOS_Table*.csv"))

data_rows = []

def parse_val(v):
    if pd.isna(v): return 0.0
    s = str(v).replace('.', '').replace(',', '.') # Handle Indonesian formatting
    try:
        return float(s)
    except:
        return 0.0

for f in all_files:
    for key, (prov, tahun) in file_map.items():
        if key in f:
            df_temp = pd.read_csv(f)
            # Find the columns
            sektor_col = df_temp.columns[0]
            bau_col = df_temp.columns[1]
            
            for _, row in df_temp.iterrows():
                sektor = str(row[sektor_col]).strip()
                if "Total" in sektor or "TotalSeluruh" in sektor or pd.isna(row[sektor_col]):
                    continue # Skip summary rows
                
                val_bau = parse_val(row[bau_col])
                
                is_agri = 1 if "Pertanian" in sektor or "Kehutanan" in sektor else 0
                is_mine = 1 if "Pertambangan" in sektor else 0
                
                data_rows.append({
                    "Provinsi": prov,
                    "Sektor": sektor,
                    "Tahun_Operasi": tahun,
                    "Latitude": prov_coords[prov][0],
                    "Longitude": prov_coords[prov][1],
                    "Is_Agri": is_agri,
                    "Is_Mine": is_mine,
                    "PDRB_BAU_RpMiliar": val_bau
                })

df = pd.DataFrame(data_rows)
print(f"    Berhasil membaca {len(df)} observasi sektoral asli.")

# 2. PERSIAPAN VARIABEL GTWR
n = len(df)
coords_s = df[['Latitude', 'Longitude']].values
coords_t = df['Tahun_Operasi'].values

X_raw = df[['Is_Agri', 'Is_Mine']].values
X_norm = (X_raw - X_raw.mean(axis=0)) / (X_raw.std(axis=0) + 1e-10)
X_norm = np.column_stack([np.ones(n), X_norm])

y = df['PDRB_BAU_RpMiliar'].values

# 3. ALGORITMA GTWR
def gauss(d, bw):
    return np.exp(-0.5 * (d / (bw + 1e-10))**2)

best_bw_s = 2.0
best_bw_t = 0.7

print("\n[2] Menjalankan Model GTWR V2 (Data Asli CREA)...")
print(f"    Bandwidth Spasial : {best_bw_s}")
print(f"    Bandwidth Temporal: {best_bw_t}")

y_hat_all, resid_all, betas_all = [], [], []

for i in range(n):
    d_s = np.sqrt(np.sum((coords_s - coords_s[i])**2, axis=1))
    d_t = np.abs(coords_t - coords_t[i])
    
    w = gauss(d_s, best_bw_s) * gauss(d_t, best_bw_t)
    W = np.diag(w)
    
    Xw = X_norm.T @ W @ X_norm
    beta = np.linalg.solve(Xw + np.eye(Xw.shape[0])*1e-6, X_norm.T @ W @ y)
    
    yhat = float(X_norm[i] @ beta)
    y_hat_all.append(yhat)
    resid_all.append(y[i] - yhat)
    betas_all.append(beta)

y_arr = np.array(y)
resid_arr = np.array(resid_all)
ss_res = np.sum(resid_arr**2)
ss_tot = np.sum((y_arr - y_arr.mean())**2)
R2 = 1 - (ss_res / (ss_tot + 1e-10))
RMSE = np.sqrt(np.mean(resid_arr**2))

print("\n--- HASIL GTWR V2 (DATA ASLI) ---")
print(f"Global R-Squared : {R2:.4f}")
print(f"RMSE             : {RMSE:.4f} Miliar Rp")

betas_arr = np.array(betas_all)
print(f"\nRata-rata Koefisien (Beta Lokal):")
print(f"  Intercept (Baseline)       : {betas_arr[:,0].mean():>8.4f}")
print(f"  Is_Agri (Dampak Pertanian) : {betas_arr[:,1].mean():>8.4f}")
print(f"  Is_Mine (Dampak Tambang)   : {betas_arr[:,2].mean():>8.4f}")

# Simpan hasil nyata
out_path = os.path.join(os.getcwd(), "GTWR_V2_Results_Asli.csv")
df['Prediksi_PDRB'] = np.round(y_hat_all, 3)
df['Residual'] = np.round(resid_arr, 3)
df.to_csv(out_path, index=False)
print(f"\n[DONE] Hasil diekspor ke: {out_path}")
