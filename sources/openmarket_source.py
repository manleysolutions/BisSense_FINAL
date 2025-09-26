import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from common import load_keywords, log_event

class OpenMarketSource:
    name = "OpenMarket"

    SITES = [
        # STATE PORTALS
        {
            "name": "Nebraska-Procurement",
            "url": "https://das.nebraska.gov/materiel/bid-opportunities.html",
            "agency": "State of Nebraska"
        },
        {
            "name": "California-CSCR",
            "url": "https://caleprocure.ca.gov/pages/index.aspx",
            "agency": "State of California"
        },
        {
            "name": "Texas-ESBD",
            "url": "https://www.txsmartbuy.com/esbd",
            "agency": "State of Texas"
        },
        {
            "name": "Florida-DMS",
            "url": "https://vendor.myfloridamarketplace.com/",
            "agency": "State of Florida"
        },
        {
            "name": "NewYork-NYSCR",
            "url": "https://www.nyscr.ny.gov/",
            "agency": "State of New York"
        },
        {
            "name": "Georgia-GPR",
            "url": "https://ssl.doas.state.ga.us/PRSapp/PR_index.jsp",
            "agency": "State of Georgia"
        },

        # CITIES / DISTRICTS
        {
            "name": "ManhattanBeach-USD",
            "url": "https://www.mbusd.org/apps/pages/bids_and_proposals",
            "agency": "MBUSD"
        },
        {
            "name": "ManhattanBeach-City",
            "url": "https://www.manhattanbeach.gov/departments/public-works/bid-opportunities",
            "agency": "City of Manhattan Beach"
        },
        {
            "name": "LAUSD",
            "url": "https://psd.lausd.org/",
            "agency": "Los Angeles Unified School District"
        },
        {
            "name": "NYC-CityRecord",
            "url": "https://a856-cityrecord.nyc.gov/",
            "agency": "City of New York"
        },
        {
            "name": "Chicago-Procurement",
            "url": "https://www.chicago.gov/city/en/depts/dps.html",
            "agency": "City of Chicago"
        },
        {
            "name": "Houston-Procurement",
            "url": "https://purchasing.houstontx.gov/",
            "agency": "City of Houston"
        }
    ]

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/122.0.0.0 Safari/537.36"
    }

    def fetch(self, days_back=30, limit=50):
        results = []
        kws = [k.lower() for k in load_keywords()]

        for site in self.SITES:
            try:
                resp = requests.get(site["url"], headers=self.HEADERS, timeout=30)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                count = 0
                for a in soup.select("a[href]"):
                    title = (a.get_text() or "").strip()
                    href = a["href"]
                    if not title:
                        continue

                    # look for RFP/Bid/Solicitation markers
                    if not re.search(r"\b(RFP|Request for Proposal|Bid|Solicitation)\b", title, re.IGNORECASE):
                        continue

                    # keyword filter
                    t_low = title.lower()
                    if not any(kw in t_low for kw in kws):
                        continue

                    url = urljoin(site["url"], href)

                    results.append({
                        "source": self.name,
                        "external_id": url,
                        "title": title,
                        "agency": site["agency"],
                        "issue_date": None,
                        "due_date": None,
                        "url": url,
                        "naics": None,
                        "keywords": title,
                        "est_value": None,
                        "status": "new",
                        "raw": {"title": title, "url": url, "agency": site["agency"]}
                    })
                    count += 1
                    if count >= limit:
                        break

                log_event("fetch", f"{site['name']} matched {count}", "success", actor=self.name)

            except Exception as e:
                log_event("fetch", f"{site['name']} error: {e}", "error", actor=self.name)

        return results
