"""
Extract markdown tables from converted .md files and save them to separate files.
"""
import re
import os

def extract_tables(md_content, source_file):
    """Extract all markdown tables from a markdown string."""
    lines = md_content.split('\n')
    tables = []
    current_table = []
    in_table = False
    table_start_line = 0

    for i, line in enumerate(lines):
        # A table line contains '|' as separator
        stripped = line.strip()
        if re.match(r'^\|.*\|$', stripped) or re.match(r'^\|[-| :]+\|$', stripped):
            if not in_table:
                in_table = True
                table_start_line = i + 1
            current_table.append(line)
        else:
            if in_table and current_table:
                # Only save if table has at least 2 rows (header + separator or more)
                if len(current_table) >= 2:
                    tables.append({
                        'start_line': table_start_line,
                        'content': '\n'.join(current_table)
                    })
                current_table = []
                in_table = False

    # Don't forget last table if file ends with one
    if in_table and current_table and len(current_table) >= 2:
        tables.append({
            'start_line': table_start_line,
            'content': '\n'.join(current_table)
        })

    return tables


def get_context_around_table(md_content, table_content, chars=300):
    """Get heading/context text before the table."""
    idx = md_content.find(table_content)
    if idx == -1:
        return ""
    # Walk back to find the nearest heading
    before = md_content[:idx]
    headings = re.findall(r'(#{1,6}\s+.+)', before)
    if headings:
        return headings[-1].strip()
    # Fallback: last non-empty line before table
    lines_before = [l.strip() for l in before.split('\n') if l.strip()]
    if lines_before:
        return lines_before[-1]
    return ""


def process_file(md_path):
    base = os.path.splitext(md_path)[0]
    output_path = base + "_tables.md"

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    tables = extract_tables(content, md_path)

    if not tables:
        print(f"[!] No tables found in: {md_path}")
        return

    print(f"[+] Found {len(tables)} table(s) in: {os.path.basename(md_path)}")

    output_lines = [
        f"# Extracted Tables from: {os.path.basename(md_path)}",
        f"\nTotal tables found: **{len(tables)}**\n",
        "---\n"
    ]

    for i, tbl in enumerate(tables, 1):
        context = get_context_around_table(content, tbl['content'])
        output_lines.append(f"## Table {i}")
        if context:
            output_lines.append(f"*Context / Heading: {context}*")
        output_lines.append(f"*(Line ~{tbl['start_line']})*\n")
        output_lines.append(tbl['content'])
        output_lines.append("\n---\n")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"    --> Saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    files = [
        "ID-CREA_CELIOS-Indonesia-Nickel-Development.md",
        "IEEFA_Report-Indonesias_nickel_companies_need_RE_Oct2024.md"
    ]

    base_dir = r"c:\Users\msi\Documents\New folder\Nickel-Spatiotemporal-GTWR-Leontief"

    for fname in files:
        full_path = os.path.join(base_dir, fname)
        if os.path.exists(full_path):
            process_file(full_path)
        else:
            print(f"[!] File not found: {full_path}")

    print("\nDone!")
