"""
Extract tables from PDF files using pdfplumber and save each table as a CSV file.
"""
import pdfplumber
import csv
import os
import re

def clean_cell(cell):
    """Clean a table cell value."""
    if cell is None:
        return ""
    return str(cell).strip().replace('\n', ' ')

def get_nearest_heading(page):
    """Try to get a meaningful label from page text."""
    try:
        text = page.extract_text() or ""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        # Look for lines that look like headings (Tabel/Table + number)
        for line in lines:
            if re.search(r'(Tabel|Table)\s*\d+', line, re.IGNORECASE):
                # Clean for filename use
                label = re.sub(r'[^\w\s\-]', '', line)
                label = re.sub(r'\s+', '_', label.strip())
                return label[:60]
        return ""
    except:
        return ""

def extract_tables_to_csv(pdf_path, output_dir):
    """Extract all tables from a PDF and save each as a separate CSV."""
    os.makedirs(output_dir, exist_ok=True)
    
    pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
    # Shorten long filenames
    if "CREA" in pdf_basename or "CELIOS" in pdf_basename:
        short_name = "CREA_CELIOS"
    elif "IEEFA" in pdf_basename:
        short_name = "IEEFA"
    else:
        short_name = pdf_basename[:20]

    saved_files = []
    table_global_idx = 0

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"  Processing {total_pages} pages...")

        for page_num, page in enumerate(pdf.pages, 1):
            tables = page.extract_tables()
            if not tables:
                continue

            heading = get_nearest_heading(page)

            for t_idx, table in enumerate(tables):
                # Filter: skip tiny/empty tables
                if len(table) < 2:
                    continue
                flat = [cell for row in table for cell in row if cell and str(cell).strip()]
                if len(flat) < 3:
                    continue

                table_global_idx += 1

                # Build filename
                if heading:
                    fname = f"{short_name}_Table{table_global_idx:02d}_p{page_num}_{heading}.csv"
                else:
                    fname = f"{short_name}_Table{table_global_idx:02d}_p{page_num}.csv"
                
                # Sanitize filename
                fname = re.sub(r'[<>:"/\\|?*]', '_', fname)
                fpath = os.path.join(output_dir, fname)

                # Clean table data
                cleaned = [[clean_cell(cell) for cell in row] for row in table]

                # Normalize column count
                num_cols = max(len(row) for row in cleaned)
                padded = [row + [''] * (num_cols - len(row)) for row in cleaned]

                # Write CSV
                with open(fpath, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerows(padded)

                saved_files.append(fpath)
                print(f"    [{table_global_idx:02d}] Page {page_num}, Table {t_idx+1}: "
                      f"{len(table)} rows x {num_cols} cols -> {fname}")

    return saved_files


if __name__ == "__main__":
    base_dir = r"c:\Users\msi\Documents\New folder\Nickel-Spatiotemporal-GTWR-Leontief"
    output_dir = os.path.join(base_dir, "tables_csv")

    files = [
        "ID-CREA_CELIOS-Indonesia-Nickel-Development-compressed.pdf",
        "IEEFA Report - Indonesia's nickel companies need RE_Oct2024.pdf",
    ]

    all_files = []
    for fname in files:
        pdf_path = os.path.join(base_dir, fname)
        if not os.path.exists(pdf_path):
            print(f"[!] File not found: {pdf_path}")
            continue
        print(f"\n[+] Processing: {fname}")
        saved = extract_tables_to_csv(pdf_path, output_dir)
        all_files.extend(saved)

    print(f"\n=== Done! {len(all_files)} CSV files saved to: {output_dir} ===")
