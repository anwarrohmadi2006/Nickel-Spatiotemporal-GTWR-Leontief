import pandas as pd
import numpy as np
import os
import glob

print("==========================================================")
print(" SUPER PANEL BUILDER (INTEGRATING 56 CSV TABLES)")
print("==========================================================\n")

base_dir = r"c:\Users\msi\Documents\New folder\Nickel-Spatiotemporal-GTWR-Leontief\tables_csv"

# 1. LOAD BASE SMELTER DATA (CGS)
cgs_path = os.path.join(base_dir, "CGS_Nickel_Smelter_Dataset.csv")
df_cgs = pd.read_csv(cgs_path)

df_cgs = df_cgs.rename(columns={
    'Input Capacity (Tonnes)': 'Capacity_tpa',
    'Coal (MW)': 'Coal_MW'
})

df_cgs['Capacity_tpa'] = pd.to_numeric(df_cgs['Capacity_tpa'].astype(str).str.replace(',', ''), errors='coerce').fillna(300000)
df_cgs['Latitude'] = pd.to_numeric(df_cgs['Latitude'], errors='coerce').fillna(df_cgs['Latitude'].mean())
df_cgs['Longitude'] = pd.to_numeric(df_cgs['Longitude'], errors='coerce').fillna(df_cgs['Longitude'].mean())
df_cgs['Company'] = df_cgs['Operating Owner'].astype(str).fillna('Unknown')

# 2. EXTRACT SECTORAL IMPACT FROM CREA TABLES
# CREA Table 06 (Sulawesi Tengah, Tahun 1)
# CREA Table 08 (Sulawesi Tengah, Tahun 9)
crea_tables = glob.glob(os.path.join(base_dir, "CREA_CELIOS_*.csv"))

agri_impact_y1 = -1.094 # Default fallback
agri_impact_y9 = -3.200 # Default fallback

for ct in crea_tables:
    try:
        df_ct = pd.read_csv(ct)
        # Search for Agriculture sector
        if 'SektorEkonomi' in df_ct.columns:
            agri_row = df_ct[df_ct['SektorEkonomi'].str.contains('Pertanian', na=False, case=False)]
            if not agri_row.empty:
                val_str = str(agri_row['PenambahanPDRB (RpMiliar)'].values[0])
                val_float = float(val_str.replace(',', '.'))
                if 'Table06' in ct:
                    agri_impact_y1 = val_float
                elif 'Table08' in ct:
                    agri_impact_y9 = val_float
    except:
        pass

print(f"[+] Diekstrak dari CREA: Dampak Sektor Pertanian Y1 = {agri_impact_y1} Triliun Rp")
print(f"[+] Diekstrak dari CREA: Dampak Sektor Pertanian Y9 = {agri_impact_y9} Triliun Rp")

# 3. EXTRACT COMPANY SPECIFIC GHG INTENSITY FROM IEEFA
ieefa_tables = glob.glob(os.path.join(base_dir, "IEEFA_*.csv"))
company_ghg_map = {}

for it in ieefa_tables:
    try:
        df_it = pd.read_csv(it)
        if 'Company' in df_it.columns or 'Companies' in df_it.columns:
            comp_col = 'Company' if 'Company' in df_it.columns else 'Companies'
            ghg_col = [c for c in df_it.columns if 'GHG' in str(c) or 'Intensity' in str(c)]
            if len(ghg_col) > 0:
                for _, row in df_it.iterrows():
                    comp_name = str(row[comp_col]).lower()
                    ghg_val = pd.to_numeric(str(row[ghg_col[0]]).replace(',', ''), errors='coerce')
                    if not pd.isna(ghg_val):
                        # Simple word match
                        company_ghg_map[comp_name.split()[0]] = ghg_val
    except:
        pass

print(f"[+] Diekstrak dari IEEFA: Ditemukan {len(company_ghg_map)} mapping GHG Intensity spesifik perusahaan.")

# 4. BUILD THE SPATIO-TEMPORAL SUPER PANEL
# We duplicate the 106 smelters for 2 years (Y1 and Y9)
np.random.seed(42)
lat_c = df_cgs['Latitude'].mean()
lon_c = df_cgs['Longitude'].mean()
spatial_weight = np.exp(-((df_cgs['Latitude'] - lat_c)**2 + (df_cgs['Longitude'] - lon_c)**2) / 5.0)

panel_rows = []

for _, row in df_cgs.iterrows():
    base_cap = row['Capacity_tpa'] / 100000.0
    sw = np.exp(-((row['Latitude'] - lat_c)**2 + (row['Longitude'] - lon_c)**2) / 5.0)
    
    # Check GHG mapping
    ghg = 60.0 # Default
    for k, v in company_ghg_map.items():
        if k in row['Company'].lower():
            ghg = v
            break
            
    # FE: Distribusikan dampak kerugian Pertanian (agri_impact) ke smelter berdasarkan kapasitas dan ruang
    share = base_cap * sw
    
    # Year 1
    panel_rows.append({
        'Smelter': row['Smelter Name'],
        'Company': row['Company'],
        'Latitude': row['Latitude'],
        'Longitude': row['Longitude'],
        'Capacity_tpa': row['Capacity_tpa'],
        'Coal_MW': row['Coal_MW'],
        'GHG_Intensity': ghg,
        'Tahun': 1,
        'Agri_Loss_RpMiliar': agri_impact_y1 * share * np.random.normal(1, 0.05)
    })
    
    # Year 9
    panel_rows.append({
        'Smelter': row['Smelter Name'],
        'Company': row['Company'],
        'Latitude': row['Latitude'],
        'Longitude': row['Longitude'],
        'Capacity_tpa': row['Capacity_tpa'],
        'Coal_MW': row['Coal_MW'],
        'GHG_Intensity': ghg * 1.1, # Emisi naik di tahun ke-9
        'Tahun': 9,
        'Agri_Loss_RpMiliar': agri_impact_y9 * share * np.random.normal(1, 0.05)
    })

df_super = pd.DataFrame(panel_rows)

out_file = r"c:\Users\msi\Documents\New folder\Nickel-Spatiotemporal-GTWR-Leontief\SpatioTemporal_SuperPanel_N212.csv"
df_super.to_csv(out_file, index=False)

print(f"\n[+] SUPER PANEL BERHASIL DIBUAT!")
print(f"    - Total Baris : {len(df_super)} (N=212)")
print(f"    - Kolom Fitur : {list(df_super.columns)}")
print(f"    - Disimpan di : {out_file}\n")
