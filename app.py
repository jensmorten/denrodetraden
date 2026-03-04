import streamlit as st
from openai import OpenAI
import pdfplumber
import tempfile
import json

# ============================================
# SETUP
# ============================================

MODEL = "gpt-5.2"

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
    ["Malvik", "Melhus", "Stjørdal", "Trondheim", "Levanger", "Orkland", "Ørland", "Verdal"]
)

uploaded_file = st.file_uploader(
    "Last opp sakliste (PDF)",
    type=["pdf"]
)

password = st.text_input(
    "Passord for analyse",
    type="password"
)

authenticated = password == st.secrets["ANALYSE_PASSWORD"]

if password and not authenticated:
    st.warning("Feil passord")

analyse_knapp = st.button("🔍 Analyser sak/ sakliste", disabled=not authenticated)


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

def split_cases_with_llm(full_text):

    prompt = f"""
    Del teksten i separate saker.

    Hvis det er flere saker, starter de med "PS X/YY" eller "PS X / YYYY".

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
# get case dandidates
# ============================================

def retrieve_candidates(query):

    results = client.vector_stores.search(
        vector_store_id=VECTOR_STORE_ID,
        query=query,
        limit=20
    )

    docs = []

    for r in results.data:
        text = r.content[0].text
        docs.append(text)

    return docs

# ============================================
# Reranking
# ============================================

def rerank_documents(query, docs):

    joined_docs = "\n\n---\n\n".join(
        [f"DOKUMENT {i+1}:\n{d}" for i, d in enumerate(docs)]
    )

    prompt = f"""
    Du får en kommunestyresak og en liste med kandidatsaker.

    Velg de 5 mest relevante sakene.

    Sak:
    {query}

    Kandidater:
    {joined_docs}

    Returner KUN nummer på de 5 beste dokumentene.
    Eksempel:
    3,7,1,9,2
    """

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    ranking = response.output_text.strip()

    indices = [int(x)-1 for x in ranking.split(",") if x.strip().isdigit()]

    reranked = [docs[i] for i in indices if i < len(docs)]

    return reranked[:5]

# ============================================
# SEARCH PER SAK
# ============================================

def search_similar_cases(tekst, kommune):

    # 1 hent kandidater
    candidates = retrieve_candidates(tekst)

    # 2 rerank
    best_docs = rerank_documents(tekst, candidates)

    context = "\n\n---\n\n".join(best_docs)

    prompt = f"""
    Du er en politisk assistent for partiet Rødt. Du skal gi et kort, strukturert, nøkternt og endelig svar uten å be brukeren om mer. 

    Bruk enkel formatering:
    - Ingen nummererte seksjoner (1), 2), 3)).
    - Unngå store overskrifter.
    - Maks én enkel overskrift per del.

    Når du svarer, følg disse reglene:
    - Ikke forklar hva du gjør.
    - Ikke legg inn generelle betraktninger om hva Rødt "typisk mener".
    - Svar konkret på saken.
    - Bruk korte avsnitt og maks 3–5 punktlister totalt.

    Oppgaver (ikke referer til oppgavene direkte, men svar sømløst):
    1. Gi en kort oppsummering (maks 5–6 linjer) av saken eller sakene.
    2. Dersom det ikke framstår som en kommunal sak (brukeren har ved en feil lasta opp noe annet), si dette og avslutt behandling. Om det er en kommunal sak, gå videre uten å nevne at det er sjekka. 
    3. List 2–3 mest relevante like saker utenfor kommunen som er valgt. Referer saken, og voteringer. Kommunen som er valgt nå er {kommune}.
    4. Deserom det er få eller ingen relevante saker utenfor kommunen kan du også nevne tidlegare saker i {kommune} dersom det er relevant. 

    Saken som er lastet opp følger:
    {tekst}

    Relevante saker:
    {context}
    """

    response = client.responses.create(
        model=MODEL,
        input=prompt,
        #tools=[
        #    {
        #        "type": "file_search",
        #        "vector_store_ids": [VECTOR_STORE_ID]
        #    }
        #]
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
            st.subheader(f"Saksnummer {case["ps"]}")

            with st.spinner("Søker lignende saker..."):
                resultat = search_similar_cases(
                    case["tekst"],
                    kommune
                )

            st.markdown(resultat)