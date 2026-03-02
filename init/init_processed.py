from pathlib import Path
import json

# ============================================
# KONFIG
# ============================================

RAW_BASE = Path("data/raw")
TRACK_FILE = Path("processed_pdfs.json")

# ============================================
# FINN ALLE PDF-AR
# ============================================

all_pdfs = []

for kommune_dir in RAW_BASE.iterdir():

    if not kommune_dir.is_dir():
        continue

    for year_dir in kommune_dir.iterdir():

        if not year_dir.is_dir():
            continue

        for pdf_file in year_dir.glob("*.pdf"):

            # Bruk relativ sti frå data/raw
            rel_path = pdf_file.relative_to(RAW_BASE).as_posix()
            all_pdfs.append(rel_path)

# Sorter for stabil output
all_pdfs = sorted(all_pdfs)

print(f"Fant {len(all_pdfs)} PDF-ar.")

# ============================================
# LAGRE JSON
# ============================================

with open(TRACK_FILE, "w", encoding="utf-8") as f:
    json.dump(all_pdfs, f, indent=2, ensure_ascii=False)

print(f"Lagret {TRACK_FILE}")