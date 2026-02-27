import os
import re
import json
import pdfplumber
from pathlib import Path
from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()


client = OpenAI()
MODEL = "gpt-4.1-mini"  # rask og billig, meir enn god nok


def extract_text_from_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def split_cases(text):
    """
    Splitter protokolltekst i saker basert på PS x/yy.
    """
    pattern = r"\n(?=PS\s\d+/\d+)"
    parts = re.split(pattern, text)

    cases = []
    for p in parts:
        p = p.strip()
        if re.match(r"^PS\s\d+/\d+", p):
            cases.append(p)

    return cases


def structure_case_with_llm(case_text, kommune, dato):
    prompt = f"""
Du får tekst fra en kommunal møteprotokoll.

Trekk ut og returner gyldig JSON med følgende felt:

- kommune
- dato
- saksnummer
- tittel
- innstilling (hvis finnes)
- vedtak
- alternative_forslag (liste med objekter: forslagsstiller, tekst)
- stemmer (hvis mulig strukturert som {{for: int, mot: int}})
- rodt_nevnt (true/false)
- rodt_kontekst (tekst der Rødt eller (R) nevnes, hvis finnes)

Returner KUN gyldig JSON. Ingen forklaring.

Kommune: {kommune}
Dato: {dato}

Tekst:
{case_text}
"""

    response = client.responses.create(
        model=MODEL,
        input=prompt,
        temperature=0
    )

    content = response.output_text.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print("⚠️ Klarte ikkje parse JSON, lagrar råtekst.")
        return {"error": "invalid_json", "raw": content}


def process_folder(input_folder, kommune):
    input_path = Path(input_folder)
    output_path = input_path.parent.parent / "structured" / kommune
    output_path.mkdir(parents=True, exist_ok=True)

    pdf_files = list(input_path.glob("*.pdf"))

    for pdf_file in tqdm(pdf_files):
        print(f"\n📄 Behandler {pdf_file.name}")

        text = extract_text_from_pdf(pdf_file)

        # Finn dato frå filnamn eller tekst (enkel variant)
        date_match = re.search(r"\d{2}\.\d{2}\.\d{4}", text)
        dato = date_match.group(0) if date_match else "ukjent"

        cases = split_cases(text)

        for case in cases:
            try:
                structured = structure_case_with_llm(case, kommune, dato)
                saksnummer = structured.get("saksnummer", "ukjent").replace("/", "_")

                out_file = output_path / f"{saksnummer}.json"

                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(structured, f, ensure_ascii=False, indent=2)

                print(f"  ✅ Lagret {out_file.name}")

            except Exception as e:
                print(f"  ❌ Feil i sak: {e}")


if __name__ == "__main__":
    # Endre denne til test-mappa di:
    process_folder('\data\malvik\2025\test',
        kommune="Malvik"
    )