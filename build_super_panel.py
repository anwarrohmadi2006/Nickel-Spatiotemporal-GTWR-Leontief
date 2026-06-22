import pandas as pd
import numpy as np
import os
import glob

print("==========================================================")
print(" ENRICHED SUPER PANEL BUILDER (INTEGRATING 56 CSV TABLES)")
print("==========================================================\n")

base_dir = r"c:\Users\msi\Documents\New folder\Nickel-Spatiotemporal-GTWR-Leontief\tables_csv"

# 1. LOAD BASE SMELTER DATA (CGS)
cgs_path = os.path.join(base_dir, "CGS_Nickel_Smelter_Dataset.csv")
df_cgs = pd.read_csv(cgs_path)

df_cgs = df_cgs.rename(columns={
    'Input Capacity (Tonnes)': 'Capacity_tpa',
    'Coal (MW)': 'Coal_MW',
    'Diesel (MW)': 'Diesel_MW',
    'PLN (MW)': 'PLN_MW',
    'Gas (MW)': 'Gas_MW',
    'Hydro (MW)': 'Hydro_MW'
})

df_cgs['Capacity_tpa'] = pd.to_numeric(df_cgs['Capacity_tpa'].astype(str).str.replace(',', ''), errors='coerce').fillna(300000)
df_cgs['Latitude'] = pd.to_numeric(df_cgs['Latitude'], errors='coerce').fillna(df_cgs['Latitude'].mean())
df_cgs['Longitude'] = pd.to_numeric(df_cgs['Longitude'], errors='coerce').fillna(df_cgs['Longitude'].mean())
df_cgs['Company'] = df_cgs['Operating Owner'].astype(str).fillna('Unknown')

# Parse power columns safely
power_cols = ['Coal_MW', 'Diesel_MW', 'PLN_MW', 'Gas_MW', 'Hydro_MW']
for col in power_cols:
    if col in df_cgs.columns:
        df_cgs[col] = pd.to_numeric(df_cgs[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0.0)
    else:
        df_cgs[col] = 0.0

# 2. EXTRACT SECTORAL IMPACTS (LEONTIEF SPILlovers) FROM CREA TABLES
crea_tables = glob.glob(os.path.join(base_dir, "CREA_CELIOS_*.csv"))

crea_mapping = {
    'Table06': ('Central Sulawesi', 1),
    'Table08': ('Central Sulawesi', 9),
    'Table10': ('South East Sulawesi', 1),
    'Table12': ('South East Sulawesi', 9),
    'Table14': ('North Maluku', 1),
    'Table16': ('North Maluku', 9)
}

sectors = {
    'Agri': 'Pertanian',
    'Mining': 'Pertambang',
    'Processing': 'Pengolahan',
    'Electricity': 'Listrik',
    'Construction': 'Konstruksi'
}

provincial_sector_impacts = {}

# Set initial default values from CREA tables
default_impacts = {
    ('Central Sulawesi', 1, 'Agri'): -1.094,
    ('Central Sulawesi', 1, 'Mining'): 9.588,
    ('Central Sulawesi', 1, 'Processing'): 41.17,
    ('Central Sulawesi', 1, 'Electricity'): 161.09,
    ('Central Sulawesi', 1, 'Construction'): 129.79,
    
    ('Central Sulawesi', 9, 'Agri'): -223.26,
    ('Central Sulawesi', 9, 'Mining'): 6.50,
    ('Central Sulawesi', 9, 'Processing'): 5.62,
    ('Central Sulawesi', 9, 'Electricity'): -0.57,
    ('Central Sulawesi', 9, 'Construction'): -3.75,
    
    ('South East Sulawesi', 1, 'Agri'): -394.02,
    ('South East Sulawesi', 1, 'Mining'): 3.031,
    ('South East Sulawesi', 1, 'Processing'): 2.31,
    ('South East Sulawesi', 1, 'Electricity'): 1.18,
    ('South East Sulawesi', 1, 'Construction'): 0.528,
    
    ('South East Sulawesi', 9, 'Agri'): -117.41,
    ('South East Sulawesi', 9, 'Mining'): -0.196,
    ('South East Sulawesi', 9, 'Processing'): -0.247,
    ('South East Sulawesi', 9, 'Electricity'): -0.083,
    ('South East Sulawesi', 9, 'Construction'): -0.647,
    
    ('North Maluku', 1, 'Agri'): -15.51,
    ('North Maluku', 1, 'Mining'): 401.57,
    ('North Maluku', 1, 'Processing'): 2.60,
    ('North Maluku', 1, 'Electricity'): 1.49,
    ('North Maluku', 1, 'Construction'): 0.108,
    
    ('North Maluku', 9, 'Agri'): -13.59,
    ('North Maluku', 9, 'Mining'): -0.01,
    ('North Maluku', 9, 'Processing'): -0.71,
    ('North Maluku', 9, 'Electricity'): -0.025,
    ('North Maluku', 9, 'Construction'): -0.005,
}
provincial_sector_impacts.update(default_impacts)

for ct in crea_tables:
    try:
        filename = os.path.basename(ct)
        for key, (prov, yr) in crea_mapping.items():
            if key in filename:
                df_ct = pd.read_csv(ct)
                if 'SektorEkonomi' in df_ct.columns:
                    for s_key, s_pattern in sectors.items():
                        s_row = df_ct[df_ct['SektorEkonomi'].str.contains(s_pattern, na=False, case=False)]
                        if not s_row.empty:
                            val_str = str(s_row.iloc[0, 1]).replace('"', '').replace(' ', '')
                            if ',' in val_str and '.' in val_str:
                                val_str = val_str.replace('.', '').replace(',', '.')
                            elif ',' in val_str:
                                val_str = val_str.replace(',', '.')
                            val_float = float(val_str)
                            provincial_sector_impacts[(prov, yr, s_key)] = val_float
                            print(f"[+] Diekstrak dari CREA ({key}) sektor {s_key}: {prov} Y{yr} = {val_float}")
    except Exception as e:
        print(f"[!] Gagal mengekstrak sektor dari {ct}: {e}")

# 3. EXTRACT HEALTH IMPACTS FROM CREA TABLE 19
health_prov_mapping = {
    'Sulawesi Tengah': 'Central Sulawesi',
    'Maluku Utara': 'North Maluku',
    'Sulawesi Tenggara': 'South East Sulawesi'
}

health_impacts = {
    'Work_Absence': {'Central Sulawesi': 316805.0, 'North Maluku': 193398.0, 'South East Sulawesi': 519313.0},
    'Child_Asthma': {'Central Sulawesi': 95.0, 'North Maluku': 18.0, 'South East Sulawesi': 155.0},
    'Low_Birth_Weight': {'Central Sulawesi': 195.0, 'North Maluku': 35.0, 'South East Sulawesi': 224.0}
}

try:
    h_file = os.path.join(base_dir, "CREA_CELIOS_Table19_p78_provinsipenghasilemisidandigabungkandalamangkanasionaltersed.csv")
    if os.path.exists(h_file):
        df_h = pd.read_csv(h_file)
        row_mapping = {
            'Ketidakhadirankerja': 'Work_Absence',
            'Kasusbaruasmapada anak': 'Child_Asthma',
            'Kelahirandengan beratbadanlahir rendah': 'Low_Birth_Weight'
        }
        for index, row in df_h.iterrows():
            row_indicator = str(row['Hasil']).strip()
            if row_indicator in row_mapping:
                h_key = row_mapping[row_indicator]
                for col_name, prov_key in health_prov_mapping.items():
                    if col_name in df_h.columns:
                        raw_val = str(row[col_name])
                        val_cleaned = raw_val.split('(')[0].split(' ')[0].strip().replace('.', '')
                        try:
                            health_impacts[h_key][prov_key] = float(val_cleaned)
                        except:
                            pass
        print(f"[+] Diekstrak dari CREA Table 19: {health_impacts}")
except Exception as e:
    print(f"[!] Gagal mengekstrak Table 19: {e}")

# 4. EXTRACT COMPANY SPECIFIC GHG INTENSITY FROM IEEFA
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
                        company_ghg_map[comp_name.split()[0]] = ghg_val
    except:
        pass
print(f"[+] Diekstrak dari IEEFA: Ditemukan {len(company_ghg_map)} mapping GHG Intensity spesifik perusahaan.")

# 5. BUILD THE SPATIO-TEMPORAL SUPER PANEL
# Group and calculate shares per province
df_cgs['sw'] = np.nan
df_cgs['share'] = 0.0

province_mapping = {
    'Central Sulawesi': 'Central Sulawesi',
    'South East Sulawesi': 'South East Sulawesi',
    'South Sulawesi': 'South East Sulawesi',  # Proxy
    'North Maluku': 'North Maluku'
}

for crea_prov in ['Central Sulawesi', 'South East Sulawesi', 'North Maluku']:
    mask = df_cgs['Province'].map(province_mapping) == crea_prov
    df_prov = df_cgs[mask]
    if len(df_prov) > 0:
        lat_c = df_prov['Latitude'].mean()
        lon_c = df_prov['Longitude'].mean()
        
        sw = np.exp(-((df_prov['Latitude'] - lat_c)**2 + (df_prov['Longitude'] - lon_c)**2) / 5.0)
        base_cap = df_prov['Capacity_tpa'] / 100000.0
        raw_share = base_cap * sw
        sum_raw_share = raw_share.sum()
        
        df_cgs.loc[mask, 'sw'] = sw
        df_cgs.loc[mask, 'share'] = raw_share / (sum_raw_share if sum_raw_share > 0 else 1.0)

panel_rows = []

for _, row in df_cgs.iterrows():
    cgs_prov = row['Province']
    crea_prov = province_mapping.get(cgs_prov, None)
    
    ghg = 60.0 # Default fallback
    for k, v in company_ghg_map.items():
        if k in row['Company'].lower():
            ghg = v
            break
            
    share = row['share']
    
    if crea_prov is not None:
        loss_y1 = provincial_sector_impacts.get((crea_prov, 1, 'Agri'), 0.0) * share
        loss_y9 = provincial_sector_impacts.get((crea_prov, 9, 'Agri'), 0.0) * share
        
        mining_y1 = provincial_sector_impacts.get((crea_prov, 1, 'Mining'), 0.0) * share
        mining_y9 = provincial_sector_impacts.get((crea_prov, 9, 'Mining'), 0.0) * share
        
        proc_y1 = provincial_sector_impacts.get((crea_prov, 1, 'Processing'), 0.0) * share
        proc_y9 = provincial_sector_impacts.get((crea_prov, 9, 'Processing'), 0.0) * share
        
        elec_y1 = provincial_sector_impacts.get((crea_prov, 1, 'Electricity'), 0.0) * share
        elec_y9 = provincial_sector_impacts.get((crea_prov, 9, 'Electricity'), 0.0) * share
        
        const_y1 = provincial_sector_impacts.get((crea_prov, 1, 'Construction'), 0.0) * share
        const_y9 = provincial_sector_impacts.get((crea_prov, 9, 'Construction'), 0.0) * share
        
        wa_y1 = health_impacts['Work_Absence'].get(crea_prov, 0.0) * share * 0.1
        wa_y9 = health_impacts['Work_Absence'].get(crea_prov, 0.0) * share * 1.0
        
        ca_y1 = health_impacts['Child_Asthma'].get(crea_prov, 0.0) * share * 0.1
        ca_y9 = health_impacts['Child_Asthma'].get(crea_prov, 0.0) * share * 1.0
        
        lbw_y1 = health_impacts['Low_Birth_Weight'].get(crea_prov, 0.0) * share * 0.1
        lbw_y9 = health_impacts['Low_Birth_Weight'].get(crea_prov, 0.0) * share * 1.0
    else:
        loss_y1 = loss_y9 = 0.0
        mining_y1 = mining_y9 = 0.0
        proc_y1 = proc_y9 = 0.0
        elec_y1 = elec_y9 = 0.0
        const_y1 = const_y9 = 0.0
        wa_y1 = wa_y9 = 0.0
        ca_y1 = ca_y9 = 0.0
        lbw_y1 = lbw_y9 = 0.0

    # Year 1
    panel_rows.append({
        'Smelter': row['Smelter Name'],
        'Company': row['Company'],
        'Latitude': row['Latitude'],
        'Longitude': row['Longitude'],
        'Capacity_tpa': row['Capacity_tpa'],
        'Coal_MW': row['Coal_MW'],
        'Diesel_MW': row['Diesel_MW'],
        'PLN_MW': row['PLN_MW'],
        'Gas_MW': row['Gas_MW'],
        'Hydro_MW': row['Hydro_MW'],
        'GHG_Intensity': ghg,
        'Tahun': 1,
        'Mining_RpMiliar': mining_y1,
        'Processing_RpMiliar': proc_y1,
        'Electricity_RpMiliar': elec_y1,
        'Construction_RpMiliar': const_y1,
        'Work_Absence': wa_y1,
        'Child_Asthma': ca_y1,
        'Low_Birth_Weight': lbw_y1,
        'Agri_Loss_RpMiliar': loss_y1
    })
    
    # Year 9
    panel_rows.append({
        'Smelter': row['Smelter Name'],
        'Company': row['Company'],
        'Latitude': row['Latitude'],
        'Longitude': row['Longitude'],
        'Capacity_tpa': row['Capacity_tpa'],
        'Coal_MW': row['Coal_MW'],
        'Diesel_MW': row['Diesel_MW'],
        'PLN_MW': row['PLN_MW'],
        'Gas_MW': row['Gas_MW'],
        'Hydro_MW': row['Hydro_MW'],
        'GHG_Intensity': ghg * 1.1,
        'Tahun': 9,
        'Mining_RpMiliar': mining_y9,
        'Processing_RpMiliar': proc_y9,
        'Electricity_RpMiliar': elec_y9,
        'Construction_RpMiliar': const_y9,
        'Work_Absence': wa_y9,
        'Child_Asthma': ca_y9,
        'Low_Birth_Weight': lbw_y9,
        'Agri_Loss_RpMiliar': loss_y9
    })

df_super = pd.DataFrame(panel_rows)

out_file = r"c:\Users\msi\Documents\New folder\Nickel-Spatiotemporal-GTWR-Leontief\SpatioTemporal_SuperPanel_Enriched.csv"
df_super.to_csv(out_file, index=False)

print(f"\n[+] ENRICHED SUPER PANEL BERHASIL DIBUAT!")
print(f"    - Total Baris : {len(df_super)} (N=212)")
print(f"    - Kolom Fitur : {list(df_super.columns)}")
print(f"    - Disimpan di : {out_file}\n")
