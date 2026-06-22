"""
Estimasi emisi CO2 per smelter nikel dari CGS Dataset
menggunakan faktor emisi IPCC sebagai proxy data emisi untuk GTWR.
"""
import csv
import os

# ── Faktor Emisi IPCC ──────────────────────────────────────────
EF_COAL    = 0.9    # tCO2/MWh (PLTU batubara)
EF_DIESEL  = 0.67   # tCO2/MWh (generator diesel)
EF_GAS     = 0.49   # tCO2/MWh (gas alam)
CF         = 0.80   # Capacity Factor captive power 80%
HOURS      = 8760   # jam/tahun

# Intensitas emisi proses dari IEEFA (tCO2/tNi)
PROCESS_INTENSITY = {
    'RKEF':    68.0,
    'HPAL':    13.4,
    'BF':      70.0,
    'SAF':     65.0,
    'STAL':    65.0,
    'OESBF':   65.0,
    'Unknown': 60.0,
}

TARGET_PROVINCES = {'Central Sulawesi', 'North Maluku', 'South East Sulawesi'}

def parse_float(val):
    try:
        return float(val) if val else 0.0
    except (ValueError, TypeError):
        return 0.0

# ── Baca CGS Dataset ───────────────────────────────────────────
fpath = r'c:\Users\msi\Documents\New folder\Nickel-Spatiotemporal-GTWR-Leontief\tables_csv\CGS_Nickel_Smelter_Dataset.csv'
with open(fpath, encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

results = []
for r in rows:
    province = r.get('Province', '')
    if province not in TARGET_PROVINCES:
        continue

    name     = r['Smelter Name']
    process  = (r.get('Process') or 'Unknown').split('/')[0].strip()
    status   = r.get('Status 2025', '')
    regency  = r.get('Regency', '')
    lat      = parse_float(r.get('Latitude'))
    lon      = parse_float(r.get('Longitude'))

    coal_mw    = parse_float(r.get('Coal (MW)'))
    diesel_mw  = parse_float(r.get('Diesel (MW)'))
    gas_mw     = parse_float(r.get('Gas (MW)'))
    hydro_mw   = parse_float(r.get('Hydro (MW)'))
    solar_mw   = parse_float(r.get('Solar (MW)'))
    ni_out     = parse_float(r.get('Ni metal equivalent (tonnes)'))
    out_cap    = parse_float(r.get('Output Capacity (Tonnes)'))

    # Emisi dari pembangkit (tCO2/tahun)
    emisi_power = (
        coal_mw   * EF_COAL   * CF * HOURS +
        diesel_mw * EF_DIESEL * CF * HOURS +
        gas_mw    * EF_GAS    * CF * HOURS
    )

    # Emisi dari intensitas proses (tCO2/tahun)
    intensity = PROCESS_INTENSITY.get(process, PROCESS_INTENSITY['Unknown'])
    emisi_intensity = ni_out * intensity if ni_out > 0 else 0

    # Pilih metode: power-based jika ada data MW, else intensity-based
    has_power_data = (coal_mw + diesel_mw + gas_mw) > 0
    emisi_final = emisi_power if has_power_data else emisi_intensity
    metode = 'Power-based' if has_power_data else 'Intensity-based'

    if emisi_final > 0:
        results.append({
            'Smelter Name': name,
            'Regency': regency,
            'Province': province,
            'Latitude': lat,
            'Longitude': lon,
            'Process': process,
            'Status 2025': status,
            'Coal_MW': coal_mw,
            'Diesel_MW': diesel_mw,
            'Gas_MW': gas_mw,
            'Hydro_MW': hydro_mw,
            'Solar_MW': solar_mw,
            'Ni_Output_tonnes': ni_out,
            'Output_Capacity_tonnes': out_cap,
            'RE_share_pct': round(100 * hydro_mw / (coal_mw + diesel_mw + gas_mw + hydro_mw + solar_mw), 1)
                            if (coal_mw + diesel_mw + gas_mw + hydro_mw + solar_mw) > 0 else 0,
            'Estimated_CO2_tpy': round(emisi_final),
            'GHG_Intensity_tCO2_per_tNi': round(emisi_final / ni_out, 1) if ni_out > 0 else intensity,
            'Estimation_Method': metode,
        })

# Sort by province, then emission
results.sort(key=lambda x: (x['Province'], -x['Estimated_CO2_tpy']))

# ── Output CSV ─────────────────────────────────────────────────
out_csv = r'c:\Users\msi\Documents\New folder\Nickel-Spatiotemporal-GTWR-Leontief\tables_csv\CGS_Emission_Estimates.csv'
fieldnames = list(results[0].keys())
with open(out_csv, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

# ── Ringkasan ──────────────────────────────────────────────────
print(f"{'='*80}")
print(f"  ESTIMASI EMISI CO2 SMELTER NIKEL - 3 PROVINSI UTAMA")
print(f"  Metode: IPCC Emission Factor + IEEFA Process Intensity")
print(f"{'='*80}")

from collections import defaultdict
by_province = defaultdict(list)
for r in results:
    by_province[r['Province']].append(r)

total_all = 0
for prov in sorted(by_province.keys()):
    smelters = by_province[prov]
    total = sum(s['Estimated_CO2_tpy'] for s in smelters)
    total_all += total
    print(f"\n[{prov}] ({len(smelters)} smelter) -- Total: {total/1e6:.2f} juta tCO2/tahun")
    print(f"  {'Smelter':<35} {'Process':<8} {'Coal MW':>8} {'Est.CO2 (tpy)':>15} {'Intensity':>10} {'Method':<16}")
    print(f"  {'-'*100}")
    for s in smelters[:8]:
        print(f"  {s['Smelter Name'][:35]:<35} {s['Process']:<8} {s['Coal_MW']:>8.0f} "
              f"{s['Estimated_CO2_tpy']:>15,} {s['GHG_Intensity_tCO2_per_tNi']:>10.1f} {s['Estimation_Method']:<16}")

print(f"\n{'='*80}")
print(f"  TOTAL EMISI 3 PROVINSI: {total_all/1e6:.2f} juta tCO2/tahun")
print(f"  Total smelter dengan estimasi: {len(results)}")
print(f"\n  Output CSV: {out_csv}")
print(f"{'='*80}")
