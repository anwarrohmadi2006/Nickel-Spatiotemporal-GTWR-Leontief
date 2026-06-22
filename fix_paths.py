import os
import glob
import re

workspace_dir = r"c:\Users\msi\Documents\New folder\Nickel-Spatiotemporal-GTWR-Leontief"

# Find all python files
py_files = glob.glob(os.path.join(workspace_dir, "**", "*.py"), recursive=True)

count = 0
for filepath in py_files:
    # Skip this script itself
    if os.path.basename(filepath) == "fix_paths.py":
        continue
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            continue

    modified = False
    
    # 1. Replace double-escaped path (four backslashes)
    pattern_4 = re.compile(r'C:\\\\Users\\\\user\\\\Downloads\\\\IMIP', re.IGNORECASE)
    four_bs_repl = workspace_dir.replace("\\", "\\\\")
    if pattern_4.search(content):
        content, n = pattern_4.subn(lambda m: four_bs_repl, content)
        modified = True
        print(f"  - Replaced double-escaped path in {os.path.basename(filepath)}")

    # 2. Replace single-escaped/raw path (two backslashes or single backslashes in raw strings)
    pattern_2 = re.compile(r'C:\\Users\\user\\Downloads\\IMIP|C:/Users/user/Downloads/IMIP', re.IGNORECASE)
    if pattern_2.search(content):
        content, n = pattern_2.subn(lambda m: workspace_dir, content)
        modified = True
        print(f"  - Replaced standard path in {os.path.basename(filepath)}")
        
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        count += 1

print(f"\n[+] Done! Corrected paths in {count} files.")
