import subprocess
import sys
import os

print("======================================================================")
print(" MASTER RUNNER: NIKEL SPATIO-TEMPORAL LEONTIEF PIPELINE")
print("======================================================================\n")

# Steps to run
steps = [
    ("1. Pembangkitan Super Panel Enriched", "build_super_panel.py"),
    ("2. Optimasi Fitur via Algoritma Genetika (GA)", "GTWR_Experiment_V2/run_ga_feature_selection.py"),
    ("3. Evaluasi Akhir Model Showdown", "GTWR_Experiment_V2/run_ultimate_showdown.py")
]

for label, script in steps:
    print(f"[*] Menjalankan {label} ({script})...")
    # Run script and print output
    result = subprocess.run([sys.executable, script], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[+] {label} BERHASIL!")
        # Print the last 15 lines of output as a summary
        lines = result.stdout.strip().split('\n')
        summary = "\n".join(lines[-15:])
        print("-" * 60)
        print(summary)
        print("-" * 60 + "\n")
    else:
        print(f"[!] {label} GAGAL!")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)

print("[SUCCESS] Seluruh pipeline selesai dieksekusi dengan aman!")
