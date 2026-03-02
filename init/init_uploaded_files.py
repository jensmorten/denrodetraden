from pathlib import Path
import json

# ============================================
# KONFIG
# ============================================

DOC_FOLDER = Path("..\\vector_docs")
TRACK_FILE = Path("vector_uploaded_files.json")

# ============================================
# FINN ALLE TXT-FILER
# ============================================

if not DOC_FOLDER.exists():
    print("vector_docs finnes ikke.")
    exit()

txt_files = sorted([f.name for f in DOC_FOLDER.glob("*.txt")])

print(f"Fant {len(txt_files)} dokumenter i vector_docs.")

# ============================================
# LAGRE TRACKING-FIL
# ============================================

with open(TRACK_FILE, "w", encoding="utf-8") as f:
    json.dump(txt_files, f, indent=2, ensure_ascii=False)

print(f"Lagret {TRACK_FILE}")
print("Disse dokumentene vil nå bli regnet som allerede lastet opp.")