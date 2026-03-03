# Den Røde Tråden
AI for koordinering av kommunestyresaker til bruk av Rødt

Teknisk løsning
Protokoller fra kommunestyremøter i utvalgte kommuner er lastet ned og ligger i /data/raw

skriptet structure.py går igjennom dokumentene, trekker ut saker og systematiserer hver sak som .json ved hjelp av en språkmodell (LLM)

skriptet build_documents.py konverterer til dokumenter som egner seg for semantisk søk. 

skriptet update_vector_store.py lagrer disse filene i en vektordatabase som tilrettelegger for raskt semantisk søk 

Appen Den Røde Tråden https://denrodetraden.streamlit.app/ lar brukeren laste opp et dokument (sak eller saksliste), finner fram lignende saker i vektordatabasen og gir brukeren tips om saker som er behandla i andre kommuner
