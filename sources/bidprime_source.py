import os
import json
from common import log_event

class BidPrimeSource:
    name = "BidPrime"

    def __init__(self, demo_mode=False):
        self.demo_mode = demo_mode
        # Future:
        # self.api_key = os.getenv("BIDPRIME_API_KEY")
        # self.base_url = os.getenv("BIDPRIME_API_URL")

    def fetch(self, days_back=7, limit=50):
        """
        Placeholder behavior:
        - If demo_mode and 'sample_bidprime.json' exists, load it to simulate.
        - Otherwise, return [].
        Later:
        - Implement authenticated API requests or CSV/XML ingestion.
        """
        results = []

        # Demo-mode JSON reader (drop a file named sample_bidprime.json next to this)
        if self.demo_mode and os.path.exists("sample_bidprime.json"):
            try:
                with open("sample_bidprime.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                for idx, op in enumerate(data[:limit]):
                    results.append({
                        "source": self.name,
                        "external_id": op.get("id") or op.get("url") or f"bidprime-{idx}",
                        "title": op.get("title", "").strip(),
                        "agency": op.get("agency", "").strip(),
                        "issue_date": op.get("issue_date"),
                        "due_date": op.get("due_date"),
                        "url": op.get("url", ""),
                        "naics": op.get("naics"),
                        "keywords": ",".join(op.get("keywords", [])) if op.get("keywords") else "",
                        "est_value": op.get("est_value"),
                        "status": "new",
                        "raw": op
                    })
                log_event("fetch", f"{self.name} demo loaded {len(results)}", "success", actor=self.name)
                return results
            except Exception as e:
                log_event("fetch", f"{self.name} demo error: {e}", "error", actor=self.name)
                return results

        # Real implementation goes here (API or file ingest)
        # If not configured yet, just skip quietly.
        log_event("fetch", f"{self.name} not configured; skipping", "skip", actor=self.name)
        return results
