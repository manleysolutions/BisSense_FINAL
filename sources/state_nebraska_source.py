import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from common import load_keywords, log_event

class NebraskaSource:
    name = "Nebraska-Procurement"
    URL = "https://das.nebraska.gov/materiel/bid-opportunities.html"

    def fetch(self, days_back=7, limit=50):
        results = []
        kws = [k.lower() for k in load_keywords()]

        try:
            resp = requests.get(self.URL, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Heuristic parser: find links likely to be RFPs, then keyword filter on title text
            links = soup.select("a[href]")
            for a in links:
                title = (a.get_text() or "").strip()
                href = a["href"]
                if not title:
                    continue

                # Common RFP-ish markers
                if not re.search(r"\b(RFP|Request\s+for\s+Proposal|Bid|Solicitation)\b", title, re.IGNORECASE):
                    continue

                # Keyword filter
                t_low = title.lower()
                if not any(kw in t_low for kw in kws):
                    continue

                url = urljoin(self.URL, href)
                results.append({
                    "source": self.name,
                    "external_id": url,  # URL as stable id for state pages
                    "title": title,
                    "agency": "State of Nebraska",
                    "issue_date": None,
                    "due_date": None,
                    "url": url,
                    "naics": None,
                    "keywords": title,
                    "est_value": None,
                    "status": "new",
                    "raw": {"title": title, "url": url}
                })

                if len(results) >= limit:
                    break

            log_event("fetch", f"{self.name} matched {len(results)}", "success", actor=self.name)
            return results
        except Exception as e:
            log_event("fetch", f"{self.name} error: {e}", "error", actor=self.name)
            return results
