from dotenv import load_dotenv
import os
from openai import OpenAI

# ==========================================
# SETUP
# ==========================================

load_dotenv()

client = OpenAI()

VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")
SEARCH_TERMS = ["værdal", "vaerdal"]

if not VECTOR_STORE_ID:
    raise ValueError("VECTOR_STORE_ID mangler i miljøvariabler")

# ==========================================
# HENT ALLE FILER (PAGINERT)
# ==========================================

def list_all_vectorstore_files(vector_store_id):
    all_files = []
    after = None

    while True:
        response = client.vector_stores.files.list(
            vector_store_id=vector_store_id,
            limit=100,
            after=after
        )

        all_files.extend(response.data)

        if not response.has_more:
            break

        after = response.data[-1].id

    return all_files

# ==========================================
# MAIN
# ==========================================

def main():
    print("🔍 Henter alle filer fra vector store...\n")

    vs_files = list_all_vectorstore_files(VECTOR_STORE_ID)

    print(f"Totalt funnet i vector store: {len(vs_files)} filer\n")

    deleted = 0

    for vs_file in vs_files:
        file_id = vs_file.id

        # Hent faktisk filinfo (her ligger filename)
        file_info = client.files.retrieve(file_id)
        filename = file_info.filename

        print(f"Fant fil: {filename}")

        if any(term in filename.lower() for term in SEARCH_TERMS):
            print(f"⚠ Sletter: {filename}")

            # Fjern fra vector store
            client.vector_stores.files.delete(
                vector_store_id=VECTOR_STORE_ID,
                file_id=file_id
            )

            # Fjern selve filen
            client.files.delete(file_id)

            deleted += 1

    print("\n================================")
    print(f"Slettet {deleted} filer.")
    print("================================")


if __name__ == "__main__":
    main()