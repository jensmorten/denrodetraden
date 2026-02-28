import re
import json
import pdfplumber
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI

# ============================================
# SETUP
# ============================================

load_dotenv()
client = OpenAI()

MODEL = "gpt-4.1"

# ============================================
# PDF
# ============================================

def extract_text_from_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


# ============================================
# SPLIT SAKER
# ============================================

def llm_split_cases(full_text):

    prompt = f"""
Del møteprotokollen i separate saker.

En sak starter med "PS X/YY".

Returner kun JSON:
[
  {{
    "ps": "PS 5/25",
    "tekst": "hele teksten for saken"
  }}
]

Tekst:
{full_text}
"""

    response = client.responses.create(
        model=MODEL,
        input=prompt,
        temperature=0
    )

    content = response.output_text.strip()
    content = content.replace("```json", "").replace("```", "").strip()

    return json.loads(content)


# ============================================
# STRUKTURER EN SAK FULLT
# ============================================

def llm_structure_case(case_text, kommune, dato):

    prompt = f"""
Du får teksten til én kommunestyresak.

Trekk ut:

1. tittel
2. innstilling
3. vedtak
4. alternative_forslag (liste med forslagsstiller + tekst)
5. voteringer

For hver votering:
- beskrivelse
- alternativer (liste med navn + stemmer)
- hvem vant (navn på alternativ med flest stemmer)

Der det er mulig:
- identifiser hvilket alternativ Rødt støttet
- angi om Rødt var på vinner- eller taper-side

Returner kun gyldig JSON i format:

{{
  "tittel": "...",
  "innstilling": "...",
  "vedtak": "...",
  "alternative_forslag": [
    {{
      "forslagsstiller": "...",
      "tekst": "..."
    }}
  ],
  "voteringer": [
    {{
      "beskrivelse": "...",
      "alternativer": [
        {{
          "navn": "...",
          "stemmer": 0
        }}
      ],
      "vinner": "...",
      "rodt": {{
        "støttet": "...",
        "var_vinner": true/false/null
      }}
    }}
  ]
}}

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
    content = content.replace("```json", "").replace("```", "").strip()

    return json.loads(content)


# ============================================
# MAIN
# ============================================

def process_folder(input_folder, kommune):

    input_path = Path(input_folder)
    output_path = Path("data/structured") / kommune
    output_path.mkdir(parents=True, exist_ok=True)

    pdf_files = list(input_path.glob("*.pdf"))

    for pdf_file in tqdm(pdf_files):

        print(f"\n📄 {pdf_file.name}")

        text = extract_text_from_pdf(pdf_file)

        date_match = re.search(r"\d{2}\.\d{2}\.\d{4}", text)
        dato = date_match.group(0) if date_match else "ukjent"

        cases = llm_split_cases(text)

        for case_obj in cases:

            ps_number = case_obj["ps"]
            case_text = case_obj["tekst"]

            structured_case = llm_structure_case(
                case_text,
                kommune,
                dato
            )

            # Flag: fremmet Rødt forslag?
            rodt_fremmet = any(
                "Rødt" in f["forslagsstiller"] or "(R" in f["forslagsstiller"]
                for f in structured_case.get("alternative_forslag", [])
            )

            structured_case["kommune"] = kommune
            structured_case["dato"] = dato
            structured_case["saksnummer_ps"] = ps_number
            structured_case["rodt_fremmet_forslag"] = rodt_fremmet

            filename = ps_number.replace("/", "_")
            out_file = output_path / f"{filename}.json"

            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(structured_case, f, ensure_ascii=False, indent=2)

            print(f"  ✅ Lagret {filename}.json")


# ============================================
# RUN
# ============================================

if __name__ == "__main__":

    process_folder(
        r"data\melhus\2026",  # <-- juster ved behov
        kommune="Malvik"
    )