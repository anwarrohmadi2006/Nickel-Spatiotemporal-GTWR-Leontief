"""
Extract tables from PDF files using pdfplumber and save as Markdown.
"""
import pdfplumber
import os
import re

def clean_cell(cell):
    """Clean a table cell value."""
    if cell is None:
        return ""
    return str(cell).strip().replace('\n', ' ')

def table_to_markdown(table):
    """Convert a pdfplumber table (list of lists) to markdown format."""
    if not table or len(table) == 0:
        return ""
    
    # Clean all cells
    cleaned = [[clean_cell(cell) for cell in row] for row in table]
    
    # Determine column widths
    num_cols = max(len(row) for row in cleaned)
    
    # Pad rows to equal length
    padded = [row + [''] * (num_cols - len(row)) for row in cleaned]
    
    if len(padded) == 0:
        return ""
    
    lines = []
    
    # Header row
    header = padded[0]
    lines.append('| ' + ' | '.join(header) + ' |')
    
    # Separator
    lines.append('| ' + ' | '.join(['---'] * num_cols) + ' |')
    
    # Data rows
    for row in padded[1:]:
        lines.append('| ' + ' | '.join(row) + ' |')
    
    return '\n'.join(lines)

def get_page_text_context(page, max_chars=500):
    """Extract text from a page to use as context."""
    try:
        text = page.extract_text() or ""
        # Try to find headings or labels near tables
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        # Return first meaningful lines as context
        return ' | '.join(lines[:5])
    except:
        return ""

def extract_tables_from_pdf(pdf_path, output_md_path):
    """Extract all tables from a PDF and write to a markdown file."""
    
    all_tables = []
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"  Processing {total_pages} pages...")
        
        for page_num, page in enumerate(pdf.pages, 1):
            tables = page.extract_tables()
            
            if tables:
                page_context = get_page_text_context(page)
                for t_idx, table in enumerate(tables):
                    # Filter out tiny/empty tables
                    if len(table) < 2:
                        continue
                    # Check if table has meaningful content
                    flat = [cell for row in table for cell in row if cell and str(cell).strip()]
                    if len(flat) < 3:
                        continue
                    
                    md_table = table_to_markdown(table)
                    if md_table:
                        all_tables.append({
                            'page': page_num,
                            'index': t_idx + 1,
                            'context': page_context,
                            'markdown': md_table,
                            'rows': len(table),
                            'cols': max(len(r) for r in table)
                        })
                        print(f"    Page {page_num}, Table {t_idx+1}: {len(table)} rows × {max(len(r) for r in table)} cols")
    
    if not all_tables:
        print(f"  [!] No tables found in {os.path.basename(pdf_path)}")
        return 0
    
    # Write output markdown
    source_name = os.path.basename(pdf_path)
    lines = [
        f"# Extracted Tables from: {source_name}",
        f"\n**Total tables extracted: {len(all_tables)}**",
        f"**Source file:** `{pdf_path}`\n",
        "---\n"
    ]
    
    for i, tbl in enumerate(all_tables, 1):
        lines.append(f"## Table {i} — Page {tbl['page']} (Table {tbl['index']} on page)")
        lines.append(f"*Rows: {tbl['rows']}, Columns: {tbl['cols']}*")
        if tbl['context']:
            lines.append(f"*Page context: {tbl['context'][:300]}*")
        lines.append("")
        lines.append(tbl['markdown'])
        lines.append("\n---\n")
    
    with open(output_md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"  --> Saved {len(all_tables)} tables to: {output_md_path}")
    return len(all_tables)


if __name__ == "__main__":
    base_dir = r"C:\Users\user\Downloads\IMIP"
    
    files = [
        {
            "pdf": "ID-CREA_CELIOS-Indonesia-Nickel-Development-compressed.pdf",
            "out": "ID-CREA_CELIOS-Indonesia-Nickel-Development_tables.md"
        },
        {
            "pdf": "IEEFA Report - Indonesia's nickel companies need RE_Oct2024.pdf",
            "out": "IEEFA_Report-Indonesias_nickel_companies_need_RE_Oct2024_tables.md"
        }
    ]
    
    total = 0
    for item in files:
        pdf_path = os.path.join(base_dir, item["pdf"])
        out_path = os.path.join(base_dir, item["out"])
        
        if not os.path.exists(pdf_path):
            print(f"[!] File not found: {pdf_path}")
            continue
        
        print(f"\n[+] Processing: {item['pdf']}")
        n = extract_tables_from_pdf(pdf_path, out_path)
        total += n
    
    print(f"\n=== Done! Total tables extracted: {total} ===")
