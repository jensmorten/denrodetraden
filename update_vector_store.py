from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import json
import os

# ============================================
# SETUP
# ============================================

load_dotenv()

VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")
MODEL = "gpt-4.1"

client = OpenAI()

DOC_FOLDER = Path("vector_docs")
TRACK_FILE = Path("vector_uploaded_files.json")

# ============================================
# LOAD TRACKING
# ============================================

if TRACK_FILE.exists():
    with open(TRACK_FILE, "r", encoding="utf-8") as f:
        uploaded_files = set(json.load(f))
else:
    uploaded_files = set()

# ============================================
# FIND NEW FILES
# ============================================

all_txt_files = sorted(DOC_FOLDER.glob("*.txt"))
new_files = [f for f in all_txt_files if f.name not in uploaded_files]

print(f"Totalt dokument i vector_docs: {len(all_txt_files)}")
print(f"Nye dokument å laste opp: {len(new_files)}")

if not new_files:
    print("Ingen nye filer. Ferdig.")
    exit()

# ============================================
# UPLOAD NEW FILES
# ============================================

file_ids = []

for txt_file in new_files:

    print(f"⬆ Laster opp {txt_file.name}")

    file = client.files.create(
        file=open(txt_file, "rb"),
        purpose="assistants"
    )

    file_ids.append(file.id)
    uploaded_files.add(txt_file.name)

# Batch-legg til i vector store
client.vector_stores.file_batches.create(
    vector_store_id=VECTOR_STORE_ID,
    file_ids=file_ids
)

print("✔ Nye filer lagt til vector store.")

# ============================================
# SAVE TRACKING
# ============================================

with open(TRACK_FILE, "w", encoding="utf-8") as f:
    json.dump(sorted(list(uploaded_files)), f, indent=2, ensure_ascii=False)

print("✔ Oppdatert tracking-fil.")