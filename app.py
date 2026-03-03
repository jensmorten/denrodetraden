import streamlit as st
from openai import OpenAI
import pdfplumber
import tempfile

# ============================================
# SETUP
# ============================================

MODEL = "gpt-4.1-mini"

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
VECTOR_STORE_ID = st.secrets["VECTOR_STORE_ID"]

client = OpenAI(api_key=OPENAI_API_KEY)

st.set_page_config(page_title="Den Røde Tråden", layout="wide")

st.title("🔴 Den Røde Tråden")
st.markdown("Dette er en app som hjelper Rødts kommunestyrerepresentater finne lignende saker i andre kommuner.")  
st.markdown("Last opp enkelt sak eller sakliste og finn lignende saker i andre kommuner.")
st.markdown("Appen søker i en database med saker som per idag inneholder behandlede saker fra 1. januar 2025 fram til februar 2026")

# ============================================
# INPUT
# ============================================

kommune = st.selectbox(
    "Velg kommune saken du laster opp er henta fra",
    ["Malvik", "Melhus", "Stjørdal", "Trondheim", "Levanger", "Orkland", "Ørland", "Værdal", "Orkland"]
)

uploaded_file = st.file_uploader(
    "Last opp sakliste (PDF)",
    type=["pdf"]
)

analyse_knapp = st.button("🔍 Analyser sak/ sakliste")

# ============================================
# PDF → TEXT
# ============================================

def extract_text_from_pdf(uploaded_file):

    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    text = ""

    with pdfplumber.open(tmp_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    return text


# ============================================
# SPLIT SAKER MED LLM
# ============================================

import json

def split_cases_with_llm(full_text):

    prompt = f"""
Del teksten i separate saker.

Hvis det er flere saker, starter de med "PS X/YY" eller PS X / YYYY.

Returner KUN gyldig JSON i format:

[
  {{
    "ps": "PS 5/25",
    "tekst": "hele teksten for saken"
  }}
]

Hvis teksten bare inneholder én sak (og saksnummer er ikke alltid tilstede, bare saksnavn),
returner liste med ett element. 

Tekst:
{full_text}
"""

    response = client.responses.create(
        model=MODEL,
        input=prompt,
        temperature=0
    )

    content = response.output_text.strip()

    # Fjern eventuelle kodeblokker
    content = content.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Fallback: antar at det er én sak
        return [{
            "ps": "Ukjent sak",
            "tekst": full_text
        }]

# ============================================
# SEARCH PER SAK
# ============================================

def search_similar_cases(tekst, kommune):

    prompt = f"""
Du er politisk analyseassistent. Oppsummer først kort saken(e) som er gitt og generelt hva Rødt kan tenkes å mene i denne saken. Vurder om det faktisk er en kommunal sak eller brukeren har lasta opp noe annet. 
Gi isåfall beskjed om dette og stopp videre behandling. 

Dersom det er et relevant saksdokument, finn saker i andre kommuner enn {kommune} som er tematisk lik teksten under. Du kan også nemne tidlegare saker i {kommune} dersom det er relevant. 

For kvar treff, oppgi:
- Kommune
- Saksnummer
- Kort hva saken handla om
- Om Rødt fremmet forslag
- Om Rødt vant eller tapte

Vurder igjen om dette bør ha innvirkning på hvordan Rødt i {kommune} bør stille seg til saken og tips til debatten.  

Du skal gi et kort, strukturert, nøkternt og endelig svar uten å be brukeren om mer. Begrens omtale til de 2-5 mest relevante og utelat treff som bare er tangensielt relevant. 

Tekst:
{tekst}
"""

    response = client.responses.create(
        model=MODEL,
        input=prompt,
        tools=[
            {
                "type": "file_search",
                "vector_store_ids": [VECTOR_STORE_ID]
            }
        ]
    )

    return response.output_text


# ============================================
# RUN
# ============================================

if analyse_knapp:

    if not uploaded_file:
        st.warning("Last opp PDF først.")
    else:

        with st.spinner("Leser PDF..."):
            full_text = extract_text_from_pdf(uploaded_file)

        with st.spinner("Splitter i saker..."):
            cases = split_cases_with_llm(full_text)

        st.success(f"Fant {len(cases)} saker.")

        for case in cases:
            st.subheader(case["ps"])

            with st.spinner("Søker liknande saker..."):
                resultat = search_similar_cases(
                    case["tekst"],
                    kommune
                )

            st.markdown(resultat)