from openai import OpenAI
from dotenv import load_dotenv

# ============================================
# SETUP
# ============================================

load_dotenv()
client = OpenAI()

VECTOR_STORE_ID = "vs_69a55846403c8191bfbf4d9a3568b1aa"  # ← bytt hvis ny

MODEL = "gpt-5.2"


# ============================================
# CORE SEARCH FUNCTION
# ============================================

def search(query, kommune=None, year=None):

    # Bygg ein eksplisitt instruks som bruker metadata-blokka i dokumentet
    full_query = f"""
Du søker i ein database med kommunestyresaker.

Alle dokument inneholder øverst:

METADATA:
kommune: ...
year: ...
saksnummer: ...
rodt_fremmet: ...

Bruk metadata aktivt i vurderinga.

"""

    if kommune:
        full_query += f"\nBegrens til kommune: {kommune}"

    if year:
        full_query += f"\nBegrens til år: {year}"

    full_query += f"\n\nOppgave:\n{query}"

    response = client.responses.create(
        model=MODEL,
        input=full_query,
        tools=[
            {
                "type": "file_search",
                "vector_store_ids": [VECTOR_STORE_ID]
            }
        ]
    )

    print("\n" + "=" * 60)
    print("SPØRSMÅL:")
    print(query)
    print("=" * 60)
    print(response.output_text)
    print("=" * 60 + "\n")


# ============================================
# TEST CASES
# ============================================

if __name__ == "__main__":

    # 1️⃣ Rødt tapte
    search(
        "List saker der Rødt fremmet forslag og var på tapende side. "
        "Oppgi saksnummer og kort forklaring.",
        kommune="Malvik",
        year="2025"
    )

    # 2️⃣ Miljøpakke
    search(
        "Finn saker som handler om miljøpakke eller transport.",
        kommune="Malvik"
    )

    # 3️⃣ Reguleringsplan
    search(
        "Finn saker om reguleringsplan eller E6."
    )

    # 4️⃣ Skolevei
    search(
        "Finn saker om skolevei.",
        kommune="Malvik"
    )