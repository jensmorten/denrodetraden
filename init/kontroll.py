import json
from pathlib import Path

BASE_PATH = Path("data/structured_v6")

def check_vote_consistency(vote):
    val = vote.get("validering", {})
    sum_for_ok = val.get("sum_for_match", True)
    sum_mot_ok = val.get("sum_mot_match", True)

    return sum_for_ok and sum_mot_ok


def run_control():

    total_votes = 0
    total_errors = 0

    print("🔍 Starter kontroll av voteringer\n")

    for kommune_folder in BASE_PATH.iterdir():

        if not kommune_folder.is_dir():
            continue

        print(f"\n🏛 Kommune: {kommune_folder.name}")

        for json_file in kommune_folder.glob("*.json"):

            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            saksnummer = data.get("saksnummer_ps")
            voteringer = data.get("voteringer", [])

            for i, vote in enumerate(voteringer):

                total_votes += 1

                if not check_vote_consistency(vote):

                    total_errors += 1

                    print("\n❌ Avvik funnet")
                    print(f"  Sak: {saksnummer}")
                    print(f"  Fil: {json_file.name}")
                    print(f"  Votering #{i+1}: {vote.get('beskrivelse')}")
                    print(f"  Stemmer for: {vote.get('stemmer_for')}")
                    print(f"  Sum parti for: {sum(vote['per_parti']['for'].values())}")
                    print(f"  Stemmer mot: {vote.get('stemmer_mot')}")
                    print(f"  Sum parti mot: {sum(vote['per_parti']['mot'].values())}")

    print("\n===================================")
    print(f"Totale voteringer: {total_votes}")
    print(f"Voteringer med avvik: {total_errors}")
    print("===================================\n")


if __name__ == "__main__":
    run_control()