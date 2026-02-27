import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

BASE = "https://prod01.elementscloud.no"
TENANT = "938726027_PROD-938726027-MELHUS"

HEADERS_API = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Tenant": TENANT
}

HEADERS_HTML = {
    "User-Agent": "Mozilla/5.0"
}

START_DATE = datetime(2025, 1, 1)


def get_meetings(year):
    url = f"{BASE}/publikum/api/PredefinedQuery/DmbMeetings?year={year}&dmbName=10"
    r = requests.get(url, headers=HEADERS_API)
    r.raise_for_status()
    return r.json()


def find_protocol_link(meeting_id):
    url = f"{BASE}/publikum/{TENANT}/DmbMeeting/{meeting_id}"
    r = requests.get(url, headers=HEADERS_HTML)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    for a in soup.find_all("a"):
        href = a.get("href", "")
        if "ShowMeetingDocument" in href and "/MP/" in href:
            return BASE + href

    return None


def download_pdf(url, filename):
    r = requests.get(url, headers=HEADERS_HTML)
    r.raise_for_status()

    with open(filename, "wb") as f:
        f.write(r.content)


def scrape_melhus_protocols():
    os.makedirs("data/raw/melhus", exist_ok=True)

    all_meetings = []
    for year in [2025, 2026]:
        all_meetings.extend(get_meetings(year))

    for m in all_meetings:
        meeting_date = datetime.fromisoformat(m["MO_START"])

        if meeting_date < START_DATE:
            continue

        meeting_id = m["MO_ID"]
        database = m["Database"]

        print(f"Henter møte {meeting_id} ({meeting_date.date()})")

        protocol_url = find_protocol_link(meeting_id)

        if not protocol_url:
            print("  Fant ingen protokoll.")
            continue

        filename = f"data/raw/melhus/{meeting_date.date()}_{meeting_id}.pdf"

        print(f"  Laster ned {protocol_url}")
        download_pdf(protocol_url, filename)

        print(f"  Lagret {filename}")


if __name__ == "__main__":
    scrape_melhus_protocols()