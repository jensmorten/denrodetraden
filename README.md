# Den Røde Tråden
Den Røde Tråden er et analyseverktøy som bruker språkmodeller (LLM) og semantisk søk for å systematisere og sammenligne kommunestyresaker på tvers av kommuner.

Målet er å gjøre det enklere å finne lignende saker behandlet i andre kommuner, se hvilke forslag som ble fremmet, analysere voteringer, identifisere når og hvordan Rødt har fremmet alternative forslag, lære av tidligere behandlinger

## App: Den Røde Tråden
Streamlit-app: 👉 https://denrodetraden.streamlit.app/

Appen lar brukeren laste opp en saksliste eller enkeltsak (PDF) og identifisere relevante saker fra andre kommuner. Appen gir brukeren mulighet til å se: tidligere vedtak, alternative forslag, voteringer, hva Rødt foreslo, om Rødt var på vinner- eller taper-side. 

Dette gjør det mulig å koordinere politikk på tvers av kommuner, lære av andre, utvikle bedre forslag, forberede alternative forslag raskt. 

## Teknisk løsning

### structure.py
skriptet structure.py Leser alle PDF-er i /data/raw/<kommune>/<år>, deler dokumentene i enkeltsaker og trekker ut:

tittel, innstilling, vedtak, alternative forslag, voteringer, stemmetall, om Rødt fremmet forslag, om Rødt var på vinner- eller taper-side og  lagrer hver sak som strukturert JSON i: /data/structured/<kommune>/

for å unngå unødvendige LLM-kall holdes det oversikt over allerede behandlede PDF-er i: processed_pdfs.json

### build_documents.py
skriptet build_documents.py leser alle JSON-saker og konverterer dem til tekst-dokumenter optimalisert for semantisk søk og lagrer disse i: /data/vector_docs/ 
Disse tekstene er laget for å gi gode embeddings og presise søketreff.

### update_vector_store.py:
build_documents.py Laster nye dokumenter opp til OpenAI Vector Store (vektordatabasen). Skriptet unngår duplikater via uploaded_docs.json


