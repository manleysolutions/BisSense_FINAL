import os
import requests
from common import load_keywords, log_event

class GoogleCSESource:
    name = "GoogleCSE"
    BASE_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.cse_id = os.getenv("GOOGLE_CSE_ID")

    def classify_opportunity(self, link, title, snippet):
        text = (title + " " + snippet).lower()

        if ".mil" in link:
            return "Military"
        if link.endswith(".gov") or ".gov/" in link:
            if any(word in text for word in ["state", "county", "city", "municipal"]):
                return "State/Local Government"
            return "Federal Government"
        if ".us" in link:
            return "State/Local Government"
        if ".edu" in link:
            return "Education"
        if any(word in text for word in ["hospital", "clinic", "health", "medical", "med center", "healthcare"]):
            return "Healthcare"
        return "Enterprise/Other"

    def fetch(self, days_back=30, limit=20):
        results = []
        if not self.api_key or not self.cse_id:
            log_event("fetch", "Google CSE not configured; skipping", "skip", actor=self.name)
            return results

        kws = load_keywords()
        queries = (
            [f"{kw} RFP site:.gov" for kw in kws] +
            [f"{kw} RFP site:.edu" for kw in kws] +
            [f"{kw} RFP site:.us" for kw in kws] +
            [f"{kw} RFP site:.mil" for kw in kws]
        )

        try:
            inserted = 0
            for q in queries:
                if inserted >= limit:
                    break

                params = {"key": self.api_key, "cx": self.cse_id, "q": q}
                resp = requests.get(self.BASE_URL, params=params, timeout=20)
                if resp.status_code != 200:
                    log_event("fetch", f"HTTP {resp.status_code} for query {q}", "error", actor=self.name)
                    continue

                data = resp.json()
                items = data.get("items", [])
                for item in items:
                    title = item.get("title", "").strip()
                    link = item.get("link", "")
                    snippet = item.get("snippet", "")

                    # Keyword + Title filter
                    text = (title + " " + snippet).lower()
                    matched = any(kw.lower() in text for kw in kws)
                    title_matched = any(kw.lower() in title.lower() for kw in kws)

                    # Domain filter
                    valid_domain = (".gov" in link or ".edu" in link or ".us" in link or ".mil" in link)

                    if not (matched and title_matched and valid_domain):
                        continue

                    # ✅ Proper classification
                    category = self.classify_opportunity(link, title, snippet)

                    results.append({
                        "source": self.name,
                        "external_id": link,
                        "title": title,
                        "agency": category,   # 👈 fixed here
                        "issue_date": None,
                        "due_date": None,
                        "url": link,
                        "naics": None,
                        "keywords": q,
                        "est_value": None,
                        "status": "new",
                        "raw": item
                    })
                    inserted += 1
                    if inserted >= limit:
                        break

            log_event("fetch", f"{self.name} matched {inserted}", "success", actor=self.name)
            return results

        except Exception as e:
            log_event("fetch", f"{self.name} error: {e}", "error", actor=self.name)
            return results
