import numpy as np
import pandas as pd
import warnings
from sklearn.svm import SVR
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import pdist, squareform

warnings.filterwarnings('ignore')

import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("==========================================================")
print(" GRAPH CONVOLUTION EXPERIMENT ON PANEL DATA (N=212)")
print("==========================================================\n")

df = pd.read_csv("SpatioTemporal_Panel_N212.csv")
n = len(df)

# 1. FEATURE MATRIX (X)
features = ['Capacity_tpa', 'Coal_MW', 'Process_Enc', 'Product_Enc']
scaler = StandardScaler()
X_raw = scaler.fit_transform(df[features].values)
y = df['Economic_Burden_RpMiliar'].values

# 2. ADJACENCY MATRIX (Spatial & Temporal Graph)
coords = df[['Latitude', 'Longitude']].values
times = df[['Tahun']].values

dist_s = squareform(pdist(coords, metric='euclidean'))
dist_t = squareform(pdist(times, metric='euclidean'))

# Graph Edges: Terhubung secara spasial dan temporal
# Jika jarak spasial sangat dekat (< 0.1 degree) dan di tahun yang sama
A = np.zeros((n, n))
for i in range(n):
    for j in range(n):
        if dist_s[i,j] < 0.2 and dist_t[i,j] == 0:
            A[i,j] = 1.0

# Normalisasi Matriks (GCN style)
D = np.diag(A.sum(axis=1) + 1e-10)
A_norm = np.linalg.inv(D) @ A
I = np.eye(n)
A_combined = I + 0.8 * A_norm

# Graph Convolution: H = A * X
X_gcn = A_combined @ X_raw
X_gcn_scaled = StandardScaler().fit_transform(X_gcn)

print(f"[1] Spatio-Temporal Graph berhasil dibangun dengan {int(A.sum())} Edges.")
print("[2] Melatih Graph Convolutional SVR (5-Fold CV)...")

kf = KFold(n_splits=5, shuffle=True, random_state=42)
y_pred_cv = np.zeros(n)

for train_idx, test_idx in kf.split(X_gcn_scaled):
    X_tr, X_te = X_gcn_scaled[train_idx], X_gcn_scaled[test_idx]
    y_tr = y[train_idx]
    
    svr = SVR(kernel='rbf', C=1000, gamma='scale')
    svr.fit(X_tr, y_tr)
    y_pred_cv[test_idx] = svr.predict(X_te)

r2_out = r2_score(y, y_pred_cv)

print("\n==========================================================")
print(f" HASIL ST-GRAPH OUT-OF-SAMPLE: {r2_out*100:.2f}%")
print("==========================================================\n")

if r2_out > 0.8822:
    print("KESIMPULAN: GRAPH MENGALAHKAN GTWR!")
else:
    print("KESIMPULAN: GRAPH GAGAL MENGEJAR GTWR (88.22%).")
    print("GTWR tetap menjadi pemegang takhta tertinggi.")
