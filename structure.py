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

MODEL = "gpt-4.1-mini"

RAW_BASE = Path("data/raw")
OUTPUT_BASE = Path("data/structured")
TRACK_FILE = Path("processed_pdfs.json")

# ============================================
# LOAD TRACKING
# ============================================

if TRACK_FILE.exists():
    with open(TRACK_FILE, "r", encoding="utf-8") as f:
        processed_pdfs = set(json.load(f))
else:
    processed_pdfs = set()

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

def safe_json_load(text):
    """
    Forsøker å parse JSON.
    Hvis det feiler pga ekstra tekst, prøver å isolere første JSON-array.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:

        # Finn første '[' og siste ']'
        start = text.find("[")
        end = text.rfind("]")

        if start != -1 and end != -1:
            candidate = text[start:end+1]
            try:
                return json.loads(candidate)
            except Exception:
                pass

        raise  # Hvis det fortsatt feiler


def llm_split_cases(full_text):

    prompt = f"""
Del møteprotokollen i separate saker.

En sak starter med "PS X/YY" eller PS X/YYYY.

Returner kun JSON.
Ingen forklarende tekst.
Kun gyldig JSON-array.

Format:
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

    try:
        return safe_json_load(content)
    except Exception as e:
        print("\n⚠️ Klarte ikke parse JSON fra llm_split_cases")
        print("Første 1000 tegn av respons:")
        print(content[:1000])
        raise e

# ============================================
# STRUKTURER EN SAK
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
- alternativer (navn + stemmer)
- hvem vant
- hvilket alternativ Rødt støttet
- om Rødt var på vinner- eller taper-side

Returner kun gyldig JSON.

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
# MAIN PIPELINE
# ============================================

def process_all():

    for kommune_dir in RAW_BASE.iterdir():

        if not kommune_dir.is_dir():
            continue

        kommune = kommune_dir.name
        print(f"\n🏛 Kommune: {kommune}")

        output_path = OUTPUT_BASE / kommune
        output_path.mkdir(parents=True, exist_ok=True)

        for year_dir in kommune_dir.iterdir():

            if not year_dir.is_dir():
                continue

            for pdf_file in tqdm(year_dir.glob("*.pdf")):

                # Bruk relativ POSIX-sti
                rel_path = pdf_file.relative_to(RAW_BASE).as_posix()

                if rel_path in processed_pdfs:
                    print(f"⏭ Hopper over {rel_path}")
                    continue

                print(f"\n📄 Behandler {rel_path}")

                # =====================================
                # PDF → TEXT
                # =====================================

                text = extract_text_from_pdf(pdf_file)

                date_match = re.search(r"\d{2}\.\d{2}\.\d{4}", text)
                dato = date_match.group(0) if date_match else "ukjent"

                # =====================================
                # SPLIT I SAKER (LLM)
                # =====================================

                cases = llm_split_cases(text)

                # =====================================
                # STRUKTURER HVER SAK (LLM)
                # =====================================

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
                      (
                        isinstance(f.get("forslagsstiller"), str)
                        and (
                        "Rødt" in f["forslagsstiller"]
                        or "(R" in f["forslagsstiller"]
                         )
                        )
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

                    print(f"  ✅ Lagret {kommune}/{filename}.json")

                # =====================================
                # LEGG TIL I TRACKING
                # =====================================

                processed_pdfs.add(rel_path)

                with open(TRACK_FILE, "w", encoding="utf-8") as f:
                    json.dump(sorted(list(processed_pdfs)), f, indent=2, ensure_ascii=False)

                print(f"✔ Ferdig med {rel_path}")


# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    process_all()