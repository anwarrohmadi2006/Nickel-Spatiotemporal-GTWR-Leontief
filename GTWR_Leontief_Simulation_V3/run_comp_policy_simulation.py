import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
import os
import warnings

warnings.filterwarnings('ignore')

print("======================================================================")
print(" COMPREHENSIVE POLICY SIMULATION V3: BAU vs RE+APC")
print("======================================================================\n")

# Paths
base_dir = r"c:\Users\msi\Documents\New folder\Nickel-Spatiotemporal-GTWR-Leontief"
csv_path = os.path.join(base_dir, "SpatioTemporal_SuperPanel_Enriched.csv")
df_panel = pd.read_csv(csv_path).fillna(0)

# 1. LOAD OPTIMAL FEATURES AND TRAIN RANDOM FOREST MODEL
# Random Forest is highly stable for out-of-bounds policy scenario extrapolation
selected_features = ['Gas_MW', 'Processing_RpMiliar', 'Electricity_RpMiliar', 'Child_Asthma', 'Tahun']
print(f"[1] Memuat {len(selected_features)} Fitur Terseleksi GA untuk Model Regresi:")
print(f"    {selected_features}\n")

# Prepare training data
X_train = df_panel[selected_features].values
# Treat the target as a positive economic burden (Agri_Burden = -Agri_Loss)
y_train = -df_panel['Agri_Loss_RpMiliar'].values

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

# Fit Random Forest Model
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X_train_scaled, y_train)
print("[+] Model Random Forest berhasil dilatih pada data panel historis (N=212).")

# 2. CONSTRUCT FUTURE POLICY SCENARIOS FOR YEAR 15 (TAHUN 15)
print("\n[2] Mensimulasikan Skenario Kebijakan Masa Depan (Tahun 15)...")

# Base Year 9 smelters as starting point for projection
df_y9 = df_panel[df_panel['Tahun'] == 9].copy()

# A. BAU Scenario (Continuous high coal captive capacity and emissions)
df_bau = df_y9.copy()
df_bau['Tahun'] = 15
df_bau['Gas_MW'] = df_y9['Gas_MW']
df_bau['Processing_RpMiliar'] = df_y9['Processing_RpMiliar'] * 1.3
df_bau['Electricity_RpMiliar'] = df_y9['Electricity_RpMiliar'] * 1.45
df_bau['Child_Asthma'] = df_y9['Child_Asthma'] * 1.5

# B. RE+APC Scenario (Energy transition: coal phase-out, clean energy expansion, health control)
df_reapc = df_y9.copy()
df_reapc['Tahun'] = 15
df_reapc['Gas_MW'] = df_y9['Gas_MW'] * 3.0
df_reapc['Processing_RpMiliar'] = df_y9['Processing_RpMiliar'] * 1.3
df_reapc['Electricity_RpMiliar'] = df_y9['Electricity_RpMiliar'] * 0.4
df_reapc['Child_Asthma'] = df_y9['Child_Asthma'] * 0.3

# Scale future inputs using training scaler parameters
X_bau_scaled = scaler.transform(df_bau[selected_features].values)
X_reapc_scaled = scaler.transform(df_reapc[selected_features].values)

# 3. PREDICT SPATIOTEMPORAL AGRICULTURAL BURDEN
print("\n[3] Memprediksi Beban Kerugian Sektor Pertanian Makro...")
y_pred_bau = rf_model.predict(X_bau_scaled)
y_pred_reapc = rf_model.predict(X_reapc_scaled)

# 4. LEONTIEF INPUT-OUTPUT & HEALTH ECONOMIC VALUATION
LEONTIEF_MULTIPLIER = 1.82

# Economic health values from CREA Table 34 (converted to Rp Miliar per unit):
ASTHMA_COST = 4.228e-3 
ABSENCE_COST = 3.353e-4

# Calculate health costs for BAU and RE+APC (in Rp Miliar)
health_cost_bau = (df_bau['Child_Asthma'] * ASTHMA_COST) + (df_y9['Work_Absence'] * 1.5 * ABSENCE_COST)
health_cost_reapc = (df_reapc['Child_Asthma'] * ASTHMA_COST) + (df_y9['Work_Absence'] * 0.4 * ABSENCE_COST)

# 5. SIMULATION SUMMARY METRICS
agri_loss_saved = np.sum(y_pred_bau) - np.sum(y_pred_reapc)  # Reduction in burden (BAU - REAPC)
leontief_grdp_saved = agri_loss_saved * LEONTIEF_MULTIPLIER
health_burden_saved = np.sum(health_cost_bau) - np.sum(health_cost_reapc)
total_economic_surplus = leontief_grdp_saved + health_burden_saved

print("\n======================================================================")
print("             HASIL AKHIR SIMULASI TRANSISI ENERGI (TAHUN 15)           ")
print("======================================================================")
print(f" Total Kerugian Sektor Pertanian (BAU)    : Rp {np.sum(y_pred_bau):.2f} Miliar")
print(f" Total Kerugian Sektor Pertanian (RE+APC) : Rp {np.sum(y_pred_reapc):.2f} Miliar")
print(f" Kerugian Pertanian yang Diselamatkan     : Rp {agri_loss_saved:.2f} Miliar")
print("----------------------------------------------------------------------")
print(f" Surplus PDRB Sektoral (Leontief x {LEONTIEF_MULTIPLIER:.2f})  : Rp {leontief_grdp_saved:.2f} Miliar")
print(f" Penghematan Beban Kesehatan Lingkungan   : Rp {health_burden_saved:.2f} Miliar")
print("----------------------------------------------------------------------")
print(f" SURPLUS EKONOMI CUMULATIVE RE+APC vs BAU : Rp {total_economic_surplus:.2f} Miliar")
print("======================================================================\n")

# Load province mappings from CGS smelter dataset
cgs_path = os.path.join(base_dir, "tables_csv", "CGS_Nickel_Smelter_Dataset.csv")
df_cgs_prov = pd.read_csv(cgs_path)[['Smelter Name', 'Province']].rename(columns={'Smelter Name': 'Smelter'}).drop_duplicates('Smelter')

# Merge Province mapping back into df_y9 to output spatial report
df_y9_merged = df_y9.merge(df_cgs_prov, on='Smelter', how='left')

# Save results to CSV
df_results = pd.DataFrame({
    'Smelter': df_y9_merged['Smelter'],
    'Province': df_y9_merged['Province'].fillna('Other'),
    'Agri_Loss_BAU_Miliar': np.round(y_pred_bau, 4),
    'Agri_Loss_REAPC_Miliar': np.round(y_pred_reapc, 4),
    'Agri_Loss_Saved_Miliar': np.round(y_pred_bau - y_pred_reapc, 4),
    'Leontief_GRDP_Saved_Miliar': np.round((y_pred_bau - y_pred_reapc) * LEONTIEF_MULTIPLIER, 4),
    'Health_Cost_Saved_Miliar': np.round(health_cost_bau.values - health_cost_reapc.values, 4)
})

out_dir = r"c:\Users\msi\Documents\New folder\Nickel-Spatiotemporal-GTWR-Leontief\GTWR_Leontief_Simulation_V3"
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

csv_out = os.path.join(out_dir, "GTWR_Leontief_Simulation_V3_Results.csv")
df_results.to_csv(csv_out, index=False)
print(f"[+] Hasil rinci spasial simulasi disimpan ke: {csv_out}")

# Write markdown report
report_out = os.path.join(out_dir, "GTWR_Leontief_Simulation_V3_Report.md")
with open(report_out, 'w', encoding='utf-8') as f:
    f.write(f"""# Laporan Simulasi: Spatio-Temporal Impacts of Energy Transition in Indonesia's Nickel Processing Industry

Laporan ini memproyeksikan dampak transisi energi di masa depan (Tahun 15) untuk meminimalkan kerugian ekonomi makro di sektor pertanian dan mereduksi beban biaya kesehatan akibat polusi captive power plants.

---

## 1. Parameter Skenario Simulasi
*   **Skenario BAU (Business as Usual):**
    *   Kapasitas batubara captive naik 45% (ekspansi batubara berlanjut).
    *   Beban asma anak-anak naik 50% akibat emisi SO2, NO2, dan PM2.5 yang memburuk.
*   **Skenario RE+APC (Transisi Energi & Transisi Bersih):**
    *   Kapasitas energi gas (`Gas_MW`) dan EBT meningkat 3 kali lipat.
    *   Aktivitas pembakaran batubara diturunkan sebesar 60%.
    *   Kasus asma ditekan hingga 70% melalui pemasangan unit pengendali polusi udara (APC / Air Pollution Control).

---

## 2. Hasil Ringkasan Simulasi Ekonomi-Lingkungan (Tahun 15)

*   **Penyelamatan Sektor Pertanian:** Rp {agri_loss_saved:.2f} Miliar (Dampak langsung terhindar).
*   **Penyelamatan PDRB Berdasarkan Koefisien Leontief (Multiplier {LEONTIEF_MULTIPLIER:.2f}):** Rp {leontief_grdp_saved:.2f} Miliar.
*   **Penghematan Beban Biaya Kesehatan Makro:** Rp {health_burden_saved:.2f} Miliar.
*   **TOTAL SURPLUS EKONOMI RE+APC VS BAU:** **Rp {total_economic_surplus:.2f} Miliar**.

---

## 3. Analisis Wilayah (Provincial Aggregation)

""")
    
    # Write provincial summary
    f.write("| Provinsi | Kerugian Pertanian BAU (Miliar Rp) | Kerugian Pertanian RE+APC (Miliar Rp) | Surplus PDRB Leontief (Miliar Rp) | Penghematan Kesehatan (Miliar Rp) |\n")
    f.write("| :--- | :---: | :---: | :---: | :---: |\n")
    for prov, grp in df_results.groupby('Province'):
        f.write(f"| {prov} | {grp['Agri_Loss_BAU_Miliar'].sum():.2f} | {grp['Agri_Loss_REAPC_Miliar'].sum():.2f} | {grp['Leontief_GRDP_Saved_Miliar'].sum():.2f} | {grp['Health_Cost_Saved_Miliar'].sum():.2f} |\n")

print(f"[+] Laporan ringkasan naratif disimpan ke: {report_out}")
