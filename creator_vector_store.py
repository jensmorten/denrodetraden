from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import json

load_dotenv()
client = OpenAI()

VECTOR_STORE_NAME = "DenRodeTraden"

def create_store():

    store = client.vector_stores.create(
        name=VECTOR_STORE_NAME
    )

    print("Vector store ID:", store.id)
    return store.id


def upload_documents(store_id):

    doc_folder = Path("vector_docs")

    file_ids = []

    for txt_file in doc_folder.glob("*.txt"):

        file = client.files.create(
            file=open(txt_file, "rb"),
            purpose="assistants"
        )

        file_ids.append(file.id)
        print(f"Lastet opp {txt_file.name}")

    client.vector_stores.file_batches.create(
        vector_store_id=store_id,
        file_ids=file_ids
    )

    print("Alle filer lastet inn.")

if __name__ == "__main__":
    store_id = create_store()
    upload_documents(store_id)