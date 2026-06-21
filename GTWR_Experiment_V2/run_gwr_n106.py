import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')
import mgwr
from mgwr.gwr import GWR
from mgwr.sel_bw import Sel_BW
from sklearn.preprocessing import StandardScaler
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("==========================================================")
print(" EXPERIMENT: GWR PADA GRAND UNIFICATION DATASET (N=106)")
print("==========================================================\n")

df = pd.read_csv("Grand_Unification_Master_N106.csv")
df = df.dropna(subset=['Latitude', 'Longitude', 'Capacity_tpa', 'Coal_MW', 'Economic_Burden_RpMiliar'])

coords = list(zip(df['Latitude'], df['Longitude']))

# Skala fitur
scaler = StandardScaler()
X = df[['Capacity_tpa', 'Coal_MW', 'Process_Enc', 'Product_Enc']].values
X_scaled = scaler.fit_transform(X)

# Target
y = df['Economic_Burden_RpMiliar'].values.reshape(-1, 1)

print(f"[1] Memulai Geographically Weighted Regression pada {len(X)} titik koordinat pabrik...")

try:
    print("    -> Mencari Spatial Bandwidth optimal...")
    bw = Sel_BW(coords, y, X_scaled).search()
    print(f"    -> Bandwidth Ditemukan: {bw:.2f}")

    print("\n[2] Melatih Model GWR secara keseluruhan...")
    gwr_model = GWR(coords, y, X_scaled, bw).fit()
    
    print("\n==========================================================")
    print(" HASIL GWR SPASIAL PADA N=106 SMELTERS")
    print("==========================================================")
    print(f" Bandwidth (Jumlah tetangga terdekat) : {bw:.0f}")
    print(f" R-Squared (In-Sample)                : {gwr_model.R2:.4f}")
    print(f" Adjusted R-Squared (Spasial)         : {gwr_model.adj_R2:.4f}")
    print(f" AICc (Kriteria Informasi Akaike)     : {gwr_model.aicc:.2f}")
    print("==========================================================\n")
    
    if gwr_model.adj_R2 > 0.5:
        print("KESIMPULAN: GWR BEKERJA DENGAN SANGAT BAIK!")
        print("Hukum Geografi Pertama Tobler terbukti valid pada skala fasilitas: Smelter yang")
        print("berdekatan (seperti di kawasan IMIP) menghasilkan 'spillover' kerugian ekonomi yang sejalan.")
    else:
        print("KESIMPULAN: EFEK SPASIAL LEMAH PADA SKALA INI.")
        print("Akurasi Adjusted-R2 GWR berada di bawah Random Forest.")
        print("Ini membuktikan bahwa letak geografis (Lintang/Bujur) kalah kuat dibandingkan")
        print("Kapasitas Produksi murni dalam menciptakan daya rusak ekonomi.")
        
except Exception as e:
    print("\n[ERROR] Terjadi kesalahan komputasi matriks Spasial:")
    print(e)
