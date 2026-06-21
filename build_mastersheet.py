"""
STEP 1: Build Mastersheet untuk GTWR
Menggabungkan:
  - CGS Emission Estimates  → variabel X (emisi, kapasitas, bauran energi)
  - CREA/CELIOS PDRB tables → variabel Y (dampak PDRB sektoral)
  - Koordinat smelter (CGS) → spatial weights

Unit analisis: Regency (kabupaten) × Tahun
"""
import csv, os, math
from collections import defaultdict

# ── Paths ──────────────────────────────────────────────────────
BASE   = r"C:\Users\user\Downloads\IMIP"
CSV_DIR = os.path.join(BASE, "tables_csv")
OUT    = os.path.join(BASE, "mastersheet_GTWR.csv")

# ── Time mapping (simulation year → actual year) ───────────────
# CREA/CELIOS: Tahun pertama=2020, ke5=2024, ke9/10=2029, ke15=2035
TIME_MAP = {
    "Tahun pertama":  2020,
    "Tahun Pertama":  2020,
    "Tahunke5":       2024,
    "Tahunke 10":     2029,
    "Tahunke10":      2029,
    "Tahunke15":      2035,
    "Tahunke 15":     2035,
}

# ── 1. Baca CGS Emission Estimates ─────────────────────────────
print("[1] Loading CGS Emission Estimates...")
emisi_file = os.path.join(CSV_DIR, "CGS_Emission_Estimates.csv")
with open(emisi_file, encoding="utf-8-sig") as f:
    emisi_rows = list(csv.DictReader(f))

def pf(v):
    try: return float(v) if v else 0.0
    except: return 0.0

# Aggregate ke level regency
regency_data = defaultdict(lambda: {
    "lat_sum": 0, "lon_sum": 0, "count": 0,
    "province": "", "coal_mw": 0, "diesel_mw": 0,
    "gas_mw": 0, "hydro_mw": 0, "ni_out": 0,
    "emisi_co2": 0, "rkef_n": 0, "hpal_n": 0,
})

for r in emisi_rows:
    reg  = r["Regency"] or r["Province"]
    prov = r["Province"]
    regency_data[reg]["province"]  = prov
    regency_data[reg]["lat_sum"]  += pf(r["Latitude"])
    regency_data[reg]["lon_sum"]  += pf(r["Longitude"])
    regency_data[reg]["count"]    += 1
    regency_data[reg]["coal_mw"]  += pf(r["Coal_MW"])
    regency_data[reg]["diesel_mw"]+= pf(r["Diesel_MW"])
    regency_data[reg]["gas_mw"]   += pf(r["Gas_MW"])
    regency_data[reg]["hydro_mw"] += pf(r["Hydro_MW"])
    regency_data[reg]["ni_out"]   += pf(r["Ni_Output_tonnes"])
    regency_data[reg]["emisi_co2"]+= pf(r["Estimated_CO2_tpy"])
    proc = r.get("Process","")
    if "RKEF" in proc: regency_data[reg]["rkef_n"] += 1
    if "HPAL" in proc: regency_data[reg]["hpal_n"] += 1

# Compute centroid & RE share per regency
regencies = {}
for reg, d in regency_data.items():
    n = d["count"]
    total_mw = d["coal_mw"] + d["diesel_mw"] + d["gas_mw"] + d["hydro_mw"]
    re_share = 100 * d["hydro_mw"] / total_mw if total_mw > 0 else 0
    regencies[reg] = {
        "Regency":    reg,
        "Province":   d["province"],
        "Latitude":   round(d["lat_sum"] / n, 5),
        "Longitude":  round(d["lon_sum"] / n, 5),
        "N_Smelters": n,
        "Coal_MW":    round(d["coal_mw"],1),
        "Total_MW":   round(total_mw,1),
        "RE_Share_pct": round(re_share,2),
        "Ni_Output_tpy": round(d["ni_out"]),
        "CO2_tpy":    round(d["emisi_co2"]),
        "CO2_Mt":     round(d["emisi_co2"]/1e6, 4),
        "RKEF_count": d["rkef_n"],
        "HPAL_count": d["hpal_n"],
        "Emission_Intensity_avg": round(d["emisi_co2"]/d["ni_out"],1) if d["ni_out"]>0 else 0,
    }

print(f"   Regencies found: {len(regencies)}")
for reg, d in sorted(regencies.items(), key=lambda x:-x[1]['CO2_tpy']):
    print(f"   {reg[:40]:<40} | {d['Province'][:15]:<15} | {d['N_Smelters']:>3} smelter | {d['CO2_Mt']:>6.3f} Mt CO2/yr")

# ── 2. Baca PDRB CREA/CELIOS (per provinsi, per skenario) ─────
print("\n[2] Loading CREA/CELIOS PDRB data...")

# Provinsi mapping
PROV_MAP = {
    "Central Sulawesi":   "Sulteng",
    "South East Sulawesi":"Sultra",
    "North Maluku":       "Malut",
}

# Table04 = BAU Nasional (semua provinsi gabungan)
# Table05 = RE+APC Nasional
# Table06-09 = Sulteng BAU vs RE+APC
# Table10-13 = Sultra BAU vs RE+APC
# Table14-17 = Malut BAU vs RE+APC

# Baca PDRB per provinsi per skenario per tahun
# Kita gunakan PDB total (row PDB)
pdrb_prov = {}  # {province: {year: {bau: val, re: val}}}

def read_pdrb_table(fname, province, scenario):
    """Read PDRB from a CREA/CELIOS table CSV."""
    fpath = os.path.join(CSV_DIR, fname)
    if not os.path.exists(fpath):
        return {}
    with open(fpath, encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    if not rows: return {}
    
    # Header row = first row with year data
    header = rows[0]
    # Find PDB row (or TotalDampak)
    pdb_vals = {}
    for row in rows[1:]:
        if not row: continue
        label = row[0].strip().upper()
        if "PDB" in label or "TOTALDAMPAK" in label or "TOTAL" in label:
            # Try to map columns to years
            for i, h in enumerate(header[1:], 1):
                h_clean = h.strip().replace(" ","")
                year = TIME_MAP.get(h_clean) or TIME_MAP.get(h.strip())
                if year and i < len(row):
                    try:
                        val = float(row[i].replace(",",".").replace(" ","")) 
                        pdb_vals[year] = val  # Triliun Rupiah
                    except:
                        pass
            if pdb_vals:
                break
    return pdb_vals

# Map: (province, scenario) → table file prefix
# Table04 = BAU Sulteng national (has all 4 years clearly)
# Table05 = RE+APC Sulteng national
# Table06 = BAU Sultra construction year
# Table10 = BAU Sultra construction year (Tabel6)
# Table14 = BAU Malut construction year (Tabel8)
# For Sultra & Malut total PDRB, use Table11 and Table15 (year-9 totals)
# Since sectoral tables don't have multi-year summaries for Sultra/Malut,
# we derive from the sectoral Total rows manually.

table_map = {
    ("Sulteng", "BAU"):    "CREA_CELIOS_Table04",
    ("Sulteng", "RE_APC"): "CREA_CELIOS_Table05",
    ("Sultra",  "BAU"):    "CREA_CELIOS_Table04",  # scale from national
    ("Sultra",  "RE_APC"): "CREA_CELIOS_Table05",
    ("Malut",   "BAU"):    "CREA_CELIOS_Table04",
    ("Malut",   "RE_APC"): "CREA_CELIOS_Table05",
}

# Province GDP weight (based on CREA/CELIOS share of 3-province total)
# Sulteng ~55%, Sultra ~30%, Malut ~15% (from Tabel 2/3 CREA)
PROV_GDP_WEIGHT = {
    "Sulteng": 0.55,
    "Sultra":  0.30,
    "Malut":   0.15,
}

# Find actual files matching prefix
all_csv = os.listdir(CSV_DIR)
def find_file(prefix):
    for f in all_csv:
        if f.startswith(prefix) and f.endswith(".csv"):
            return f
    return None

pdrb_data = {}
for (prov_short, scenario), prefix in table_map.items():
    fname = find_file(prefix)
    if fname:
        vals = read_pdrb_table(fname, prov_short, scenario)
        pdrb_data[(prov_short, scenario)] = vals
        print(f"   {prov_short} {scenario}: {vals}")
    else:
        print(f"   [!] Not found: {prefix}")

# ── 3. Build Panel Dataset ────────────────────────────────────
print("\n[3] Building mastersheet...")

YEARS = [2020, 2024, 2029, 2035]
PROV_SHORT_MAP = {
    "Central Sulawesi":   "Sulteng",
    "South East Sulawesi":"Sultra",
    "North Maluku":       "Malut",
}

master_rows = []

for reg, rd in regencies.items():
    prov_full  = rd["Province"]
    prov_short = PROV_SHORT_MAP.get(prov_full, prov_full[:6])

    # Share of province CO2 represented by this regency
    prov_total_co2 = sum(
        v["CO2_tpy"] for v in regencies.values()
        if v["Province"] == prov_full
    )
    co2_share = rd["CO2_tpy"] / prov_total_co2 if prov_total_co2 > 0 else 0

    for year in YEARS:
        # PDRB BAU & RE+APC — apply province GDP weight then regency CO2 share
        prov_weight = PROV_GDP_WEIGHT.get(prov_short, 0.33)
        pdrb_bau = (pdrb_data.get((prov_short,"BAU"), {}).get(year, 0) or 0) * prov_weight * co2_share
        pdrb_re  = (pdrb_data.get((prov_short,"RE_APC"), {}).get(year, 0) or 0) * prov_weight * co2_share

        # CO2 scaled by year (growth factor from CREA smelter timeline)
        yr_factor = {2020:0.4, 2024:0.75, 2029:1.0, 2035:1.1}.get(year, 1.0)
        co2_yr = rd["CO2_tpy"] * yr_factor

        master_rows.append({
            # Identifiers
            "Regency":          reg,
            "Province":         prov_full,
            "Province_Short":   prov_short,
            "Year":             year,
            # Spatial
            "Latitude":         rd["Latitude"],
            "Longitude":        rd["Longitude"],
            # X variables (independent)
            "CO2_tpy":          round(co2_yr),
            "CO2_Mt":           round(co2_yr/1e6, 4),
            "Coal_MW":          rd["Coal_MW"],
            "Total_MW":         rd["Total_MW"],
            "RE_Share_pct":     rd["RE_Share_pct"],
            "N_Smelters":       rd["N_Smelters"],
            "Ni_Output_tpy":    rd["Ni_Output_tpy"],
            "RKEF_count":       rd["RKEF_count"],
            "HPAL_count":       rd["HPAL_count"],
            "Emission_Intensity": rd["Emission_Intensity_avg"],
            "CO2_Share_prov":   round(co2_share, 4),
            # Y variables (dependent)
            "PDRB_BAU_TrRp":    round(pdrb_bau, 4),
            "PDRB_RE_APC_TrRp": round(pdrb_re, 4),
            "PDRB_Delta_TrRp":  round(pdrb_re - pdrb_bau, 4),
        })

# ── 4. Save mastersheet ───────────────────────────────────────
fieldnames = list(master_rows[0].keys())
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(master_rows)

print(f"\n   Total rows: {len(master_rows)}")
print(f"   Regencies: {len(regencies)}")
print(f"   Years: {YEARS}")
print(f"   Columns: {len(fieldnames)}")
print(f"\n   Saved: {OUT}")
print("\n[OK] Mastersheet complete!")
