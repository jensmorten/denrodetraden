import requests

BASE = "https://prod01.elementscloud.no/publikum/api"
TENANT = "938726027_PROD-938726027-MELHUS"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Tenant": TENANT
}

candidates = [
    "DmbMeetingDocuments/GetByMeetingId/219",
    "DmbDocuments/GetByMeetingId/219",
    "MeetingDocuments/GetByMeetingId/219",
    "Documents/GetByMeetingId/219"
]

for c in candidates:
    url = f"{BASE}/{c}"
    r = requests.get(url, headers=HEADERS)
    print(c, r.status_code)