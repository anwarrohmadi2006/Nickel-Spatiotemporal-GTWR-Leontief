"""
GTWR - Geographically and Temporally Weighted Regression
Variabel Y  = PDRB_BAU_TrRp
Variabel X  = CO2_Mt, RE_Share_pct, Coal_MW, N_Smelters, Emission_Intensity
"""
import sys
import os
import math
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Force UTF-8 output on Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ---- Paths -----------------------------------------------------------
MASTER  = r"C:\Users\user\Downloads\IMIP\mastersheet_GTWR.csv"
OUT_DIR = r"C:\Users\user\Downloads\IMIP"

# ---- Load data -------------------------------------------------------
print("[1] Loading mastersheet...")
df = pd.read_csv(MASTER, encoding='utf-8-sig')
print(f"    Shape: {df.shape}")
print(f"    Regencies: {df['Regency'].nunique()}")
print(f"    Years: {sorted(df['Year'].unique().tolist())}")
print(df[['Regency','Province','Year','CO2_Mt','RE_Share_pct','PDRB_BAU_TrRp']].head(8).to_string())
print()

# ---- Feature engineering --------------------------------------------
df_model = df.copy()
n = len(df_model)

# Normalize Year
yr_min = df_model['Year'].min()
yr_max = df_model['Year'].max()
df_model['Year_norm'] = (df_model['Year'] - yr_min) / (yr_max - yr_min + 1e-10)

# Normalize coords
df_model['Lat_norm'] = (df_model['Latitude']  - df_model['Latitude'].mean())  / (df_model['Latitude'].std()  + 1e-10)
df_model['Lon_norm'] = (df_model['Longitude'] - df_model['Longitude'].mean()) / (df_model['Longitude'].std() + 1e-10)

# Variables
X_cols = ['CO2_Mt', 'RE_Share_pct', 'Coal_MW', 'N_Smelters', 'Emission_Intensity']
Y_col  = 'PDRB_BAU_TrRp'

X_raw  = df_model[X_cols].fillna(0).values
y      = df_model[Y_col].fillna(0).values

# Standardize X
X_mean = X_raw.mean(axis=0)
X_std  = X_raw.std(axis=0) + 1e-10
X_norm = (X_raw - X_mean) / X_std
X_norm = np.column_stack([np.ones(n), X_norm])   # prepend intercept

coords_s = df_model[['Lat_norm','Lon_norm']].values
coords_t = df_model['Year_norm'].values

var_names = ['Intercept'] + X_cols

# ---- Kernel ----------------------------------------------------------
def gauss(d, bw):
    return np.exp(-0.5 * (d / (bw + 1e-10))**2)

def gtwr_cv(bw_s, bw_t):
    """Leave-one-out CV score."""
    score = 0.0
    for i in range(n):
        d_s = np.sqrt(np.sum((coords_s - coords_s[i])**2, axis=1))
        d_t = np.abs(coords_t - coords_t[i])
        w   = gauss(d_s, bw_s) * gauss(d_t, bw_t)
        w[i] = 0.0
        if w.sum() < 1e-10:
            continue
        W  = np.diag(w)
        Xw = X_norm.T @ W @ X_norm
        try:
            beta  = np.linalg.solve(Xw + np.eye(Xw.shape[0]) * 1e-6, X_norm.T @ W @ y)
            score += (y[i] - X_norm[i] @ beta) ** 2
        except np.linalg.LinAlgError:
            score += 1e12
    return score

# ---- Bandwidth selection (grid search) ------------------------------
print("[2] Selecting optimal bandwidths via CV...")
bw_s_grid = [0.3, 0.5, 0.8, 1.0, 1.5, 2.0]
bw_t_grid = [0.2, 0.3, 0.5, 0.8, 1.0]

best_cv, best_bw_s, best_bw_t = float('inf'), 1.0, 0.5

for bw_s in bw_s_grid:
    for bw_t in bw_t_grid:
        cv = gtwr_cv(bw_s, bw_t)
        marker = " <-- best" if cv < best_cv else ""
        print(f"    bw_s={bw_s:.1f}  bw_t={bw_t:.1f}  CV={cv:10.4f}{marker}")
        if cv < best_cv:
            best_cv, best_bw_s, best_bw_t = cv, bw_s, bw_t

print(f"\n    Optimal: bw_spatial={best_bw_s}, bw_temporal={best_bw_t}  (CV={best_cv:.4f})")

# ---- Run GTWR -------------------------------------------------------
print("\n[3] Running GTWR with optimal bandwidths...")

results    = []
betas_all  = []
y_hat_all  = []
resid_all  = []

for i in range(n):
    d_s = np.sqrt(np.sum((coords_s - coords_s[i])**2, axis=1))
    d_t = np.abs(coords_t - coords_t[i])
    w   = gauss(d_s, best_bw_s) * gauss(d_t, best_bw_t)

    W  = np.diag(w)
    Xw = X_norm.T @ W @ X_norm
    try:
        beta = np.linalg.solve(Xw + np.eye(Xw.shape[0]) * 1e-6, X_norm.T @ W @ y)
    except np.linalg.LinAlgError:
        beta = np.zeros(X_norm.shape[1])

    yhat  = float(X_norm[i] @ beta)
    resid = float(y[i]) - yhat

    # Local R2
    y_w   = w * y
    wsum  = w.sum() + 1e-10
    ymw   = y_w.sum() / wsum
    ss_t  = float((w * (y - ymw)**2).sum())
    ss_r  = float((w * (y - X_norm @ beta)**2).sum())
    r2_loc = 1.0 - ss_r / (ss_t + 1e-10)

    row = df_model.iloc[i]
    rec = {
        'Regency':      row['Regency'],
        'Province':     row['Province'],
        'Year':         int(row['Year']),
        'Latitude':     float(row['Latitude']),
        'Longitude':    float(row['Longitude']),
        'CO2_Mt':       float(row['CO2_Mt']),
        'RE_Share_pct': float(row['RE_Share_pct']),
        'Coal_MW':      float(row['Coal_MW']),
        'Y_actual':     round(float(y[i]), 4),
        'Y_fitted':     round(yhat, 4),
        'Residual':     round(resid, 4),
        'R2_local':     round(r2_loc, 4),
    }
    for j, vn in enumerate(var_names):
        rec[f'beta_{vn}'] = round(float(beta[j]), 6)

    results.append(rec)
    betas_all.append(beta)
    y_hat_all.append(yhat)
    resid_all.append(resid)

# ---- Global stats ---------------------------------------------------
y_arr    = np.array([float(v) for v in y])
yhat_arr = np.array(y_hat_all)
resid_arr= np.array(resid_all)

ss_res = float(np.sum(resid_arr**2))
ss_tot = float(np.sum((y_arr - y_arr.mean())**2))
R2     = 1.0 - ss_res / (ss_tot + 1e-10)
RMSE   = math.sqrt(ss_res / n)
MAE    = float(np.mean(np.abs(resid_arr)))

# ---- Print summary --------------------------------------------------
SEP = "=" * 70
sep = "-" * 70

print(f"\n{SEP}")
print(f"  GTWR RESULTS SUMMARY")
print(f"{SEP}")
print(f"  Observations      : {n}")
print(f"  Bandwidth spatial : {best_bw_s}")
print(f"  Bandwidth temporal: {best_bw_t}")
print(f"  Global R-squared  : {R2:.4f}")
print(f"  RMSE (Triliun Rp) : {RMSE:.4f}")
print(f"  MAE  (Triliun Rp) : {MAE:.4f}")
print(f"{SEP}")

betas_arr = np.array(betas_all)
print(f"\n  LOCAL BETA COEFFICIENTS (Mean +/- Std)")
print(f"  {sep}")
print(f"  {'Variable':<26} {'Mean':>9} {'Std':>9} {'Min':>9} {'Max':>9}  Interpretation")
print(f"  {sep}")
interp = {
    'Intercept':        'Baseline PDRB impact',
    'CO2_Mt':           'Higher emisi -> more PDRB impact',
    'RE_Share_pct':     'RE share -> PDRB effect',
    'Coal_MW':          'Coal capacity -> PDRB',
    'N_Smelters':       'Smelter count effect',
    'Emission_Intensity':'tCO2/tNi -> PDRB',
}
for j, vn in enumerate(var_names):
    b = betas_arr[:, j]
    print(f"  {vn:<26} {b.mean():>9.4f} {b.std():>9.4f} {b.min():>9.4f} {b.max():>9.4f}  {interp.get(vn,'')}")

print(f"\n  PREDICTIONS BY REGENCY & YEAR")
print(f"  {sep}")
print(f"  {'Regency':<28} {'Year':>5} {'Y_actual':>10} {'Y_fitted':>10} {'Resid':>8} {'R2_loc':>7}")
print(f"  {sep}")
df_res = pd.DataFrame(results)
for _, row in df_res.sort_values(['Province','Regency','Year']).iterrows():
    print(f"  {str(row['Regency'])[:28]:<28} {int(row['Year']):>5} "
          f"{row['Y_actual']:>10.4f} {row['Y_fitted']:>10.4f} "
          f"{row['Residual']:>8.4f} {row['R2_local']:>7.4f}")

# ---- Province summary -----------------------------------------------
print(f"\n  PROVINCE SUMMARY (mean across years)")
print(f"  {sep}")
print(f"  {'Province':<25} {'Mean_Y':>9} {'Mean_Yhat':>10} {'Mean_R2':>9} {'N':>4}")
print(f"  {sep}")
for prov, grp in df_res.groupby('Province'):
    print(f"  {prov[:25]:<25} {grp['Y_actual'].mean():>9.4f} {grp['Y_fitted'].mean():>10.4f} "
          f"{grp['R2_local'].mean():>9.4f} {len(grp):>4}")

# ---- Key finding ----------------------------------------------------
beta_co2_mean  = betas_arr[:, 1].mean()
beta_re_mean   = betas_arr[:, 2].mean()
direction_co2  = "positif" if beta_co2_mean > 0 else "negatif"
direction_re   = "positif" if beta_re_mean  > 0 else "negatif"

print(f"\n  KEY FINDINGS:")
print(f"    - Emisi CO2 berpengaruh {direction_co2} terhadap PDRB (beta={beta_co2_mean:.4f})")
print(f"    - RE share berpengaruh {direction_re} terhadap PDRB (beta={beta_re_mean:.4f})")
print(f"    - Model GTWR menjelaskan {R2*100:.1f}% variasi dampak PDRB")
print(f"    - RMSE = {RMSE:.4f} Triliun Rp")

# ---- Save -----------------------------------------------------------
out_results = os.path.join(OUT_DIR, "GTWR_Results.csv")
out_summary = os.path.join(OUT_DIR, "GTWR_Summary.csv")

df_res.to_csv(out_results, index=False, encoding='utf-8-sig')

summary_rows = []
for j, vn in enumerate(var_names):
    b = betas_arr[:, j]
    summary_rows.append({
        'Variable':      vn,
        'Beta_Mean':     round(float(b.mean()), 6),
        'Beta_Std':      round(float(b.std()),  6),
        'Beta_Min':      round(float(b.min()),  6),
        'Beta_Max':      round(float(b.max()),  6),
        'Pct_Positive':  round(float(100 * np.mean(b > 0)), 1),
    })
global_row = {
    'Variable':    'MODEL_GLOBAL',
    'Beta_Mean':   round(R2, 4),
    'Beta_Std':    round(RMSE, 4),
    'Beta_Min':    round(MAE, 4),
    'Beta_Max':    float(n),
    'Pct_Positive': round(best_bw_s, 2),
}
summary_rows.append(global_row)
pd.DataFrame(summary_rows).to_csv(out_summary, index=False, encoding='utf-8-sig')

print(f"\n  Output files:")
print(f"    {out_results}")
print(f"    {out_summary}")
print(f"\n[DONE] GTWR analysis complete!")
