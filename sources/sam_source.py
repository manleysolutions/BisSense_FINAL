# sources/sam_source.py
import os
import requests
import datetime
import time

class SAMSource:
    def __init__(self):
        self.name = "SAM.gov"
        self.api_key = os.getenv("SAM_API_KEY")
        if not self.api_key:
            raise ValueError("Missing SAM_API_KEY environment variable")

    def fetch(self, days_back=30, limit=50):
        base_url = "https://api.sam.gov/prod/opportunities/v1/search"
        posted_from = (datetime.date.today() - datetime.timedelta(days=days_back)).strftime("%m/%d/%Y")

        params = {
            "api_key": self.api_key,
            "postedFrom": posted_from,
            "limit": limit,
            "ptype": "o"
        }

        retries = 5
        backoff = 2
        for attempt in range(1, retries + 1):
            try:
                resp = requests.get(base_url, params=params, timeout=30)
                if resp.status_code == 429:
                    print(f"⚠️ SAM.gov rate limit hit (attempt {attempt}/{retries}), retrying in {backoff}s...")
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                resp.raise_for_status()
                data = resp.json()
                break
            except requests.RequestException as e:
                if attempt == retries:
                    raise RuntimeError(f"SAM.gov fetch failed after {retries} retries: {e}")
                print(f"⚠️ SAM.gov error {e} (attempt {attempt}/{retries}), retrying in {backoff}s...")
                time.sleep(backoff)
                backoff *= 2
        else:
            return []

        results = []
        for item in data.get("opportunitiesData", []):
            results.append({
                "title": item.get("title"),
                "agency": item.get("organizationName"),
                "source": self.name,
                "issue_date": item.get("postedDate"),
                "due_date": item.get("responseDate"),
                "url": item.get("uiLink"),
                "category": None,
                "category_weight": 0,
                "raw": item
            })
        return results
