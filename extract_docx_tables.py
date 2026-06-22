"""
Extract tables from a .docx file using python-docx and save each as a CSV file.
"""
import csv
import os
import glob
import re
from docx import Document

def clean_cell(cell_text):
    """Clean cell text."""
    return cell_text.strip().replace('\n', ' ').replace('\r', '')

def get_table_context(doc, table_idx):
    """Try to find the paragraph/heading immediately before the table."""
    # Collect all block-level elements in order
    body = doc.element.body
    elements = list(body)
    
    # Find the table element
    tables_seen = 0
    for i, elem in enumerate(elements):
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'tbl':
            if tables_seen == table_idx:
                # Look backwards for a paragraph
                for j in range(i - 1, max(i - 5, -1), -1):
                    prev_tag = elements[j].tag.split('}')[-1] if '}' in elements[j].tag else elements[j].tag
                    if prev_tag == 'p':
                        text = ''.join(r.text for r in elements[j].iter() if r.tag.split('}')[-1] == 'r' if hasattr(r, 'text') and r.text)
                        text = text.strip()
                        if text:
                            return text
                return ""
            tables_seen += 1
    return ""

def extract_tables_from_docx(docx_path, output_dir):
    """Extract all tables from a DOCX and save each as a CSV."""
    os.makedirs(output_dir, exist_ok=True)
    
    doc = Document(docx_path)
    tables = doc.tables
    print(f"  Found {len(tables)} table(s) in document")
    
    saved = []
    short_name = "Anwar_Rohmadi"

    for idx, table in enumerate(tables):
        # Extract rows
        rows = []
        for row in table.rows:
            cells = [clean_cell(cell.text) for cell in row.cells]
            rows.append(cells)

        # Skip empty/tiny tables
        flat = [c for r in rows for c in r if c]
        if len(flat) < 3 or len(rows) < 2:
            print(f"    [skip] Table {idx+1}: too small or empty")
            continue

        # Normalize column count
        num_cols = max(len(r) for r in rows)
        padded = [r + [''] * (num_cols - len(r)) for r in rows]

        # Get context
        context = get_table_context(doc, idx)
        # Sanitize for filename
        if context:
            ctx_clean = re.sub(r'[^\w\s]', '', context)
            ctx_clean = re.sub(r'\s+', '_', ctx_clean.strip())[:60]
        else:
            ctx_clean = ""

        # Build filename
        if ctx_clean:
            fname = f"{short_name}_Table{idx+1:02d}_{ctx_clean}.csv"
        else:
            fname = f"{short_name}_Table{idx+1:02d}.csv"
        fname = re.sub(r'[<>:"/\\|?*]', '_', fname)
        fpath = os.path.join(output_dir, fname)

        with open(fpath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerows(padded)

        saved.append(fpath)
        print(f"    [{idx+1:02d}] {len(rows)} rows x {num_cols} cols -> {fname}")

    return saved


if __name__ == "__main__":
    # Use glob to handle special characters (apostrophe) in filename
    matches = glob.glob(r"c:\Users\msi\Documents\New folder\Nickel-Spatiotemporal-GTWR-Leontief\Anwar*.docx")
    if not matches:
        print("[!] DOCX file not found!")
        exit(1)
    docx_path = matches[0]
    output_dir = r"c:\Users\msi\Documents\New folder\Nickel-Spatiotemporal-GTWR-Leontief\tables_csv"

    print(f"[+] Processing: {os.path.basename(docx_path)}")
    saved = extract_tables_from_docx(docx_path, output_dir)
    print(f"\n=== Done! {len(saved)} CSV files saved to: {output_dir} ===")
