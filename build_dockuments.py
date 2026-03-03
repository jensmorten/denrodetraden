import json
from pathlib import Path

BASE_PATH = Path("data/structured")

def ensure_string(value):
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    if isinstance(value, str):
        return value
    return ""

def build_document(data):

    kommune = data.get("kommune")
    dato = data.get("dato")
    year = dato.split(".")[-1] if "." in dato else "ukjent"
    saksnummer = data.get("saksnummer_ps")
    rodt_fremmet = data.get("rodt_fremmet_forslag")

    parts = []

    # 🔴 METADATA BLOKK
    parts.append("METADATA:")
    parts.append(f"kommune: {kommune}")
    parts.append(f"year: {year}")
    parts.append(f"saksnummer: {saksnummer}")
    parts.append(f"rodt_fremmet: {rodt_fremmet}")
    parts.append("---\n")

    # 🔴 Innhold
    parts.append(f"Tittel: {data.get('tittel')}")

    if data.get("vedtak"):
        #parts.append("\nVedtak:\n" + data["vedtak"])
        parts.append("\nVedtak:\n" + ensure_string(data.get("vedtak")))

    if data.get("alternative_forslag"):
        parts.append("\nAlternative forslag:")
        for f in data["alternative_forslag"]:
            parts.append(f"- {f['forslagsstiller']}: {f['tekst']}")

    if data.get("voteringer"):
        parts.append("\nVoteringer:")
        for v in data["voteringer"]:
            parts.append(f"- {v.get('beskrivelse')}")
            for alt in v.get("alternativer", []):
                stemmer = alt.get("stemmer")
                if stemmer is None:
                    stemmer_str = "ukjent"
                elif isinstance(stemmer, int):
                    stemmer_str = f"{stemmer} stemmer"
                else:
                    stemmer_str = str(stemmer)

                parts.append(f"  - {alt.get('navn', 'Ukjent')}: {stemmer_str}")

    return "\n".join(parts)


def export_all_documents(output_folder="vector_docs"):

    output_path = Path(output_folder)
    output_path.mkdir(exist_ok=True)

    for kommune_folder in BASE_PATH.iterdir():
        if not kommune_folder.is_dir():
            continue

        kommune = kommune_folder.name

        for json_file in kommune_folder.glob("*.json"):

            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            doc_text = build_document(data)

            dato = data.get("dato", "ukjent")
            year = dato.split(".")[-1] if "." in dato else "ukjent"

            saksnummer = data.get("saksnummer_ps", "ukjent")
            saksnummer_clean = saksnummer.replace("/", "_").replace(" ", "")

            filename = f"{kommune}_{year}_{saksnummer_clean}.txt"

            out_file = output_path / filename

            with open(out_file, "w", encoding="utf-8") as f:
                f.write(doc_text)

            print(f"✅ Laget dokument {filename}")


if __name__ == "__main__":
    export_all_documents()