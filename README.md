\# BidSense – Phase 1 (Find)



\## Overview

BidSense is an AI-driven RFP discovery and bidding pipeline.  

Phase 1 builds a robust \*\*Find engine\*\* that pulls opportunities from:

\- \*\*SAM.gov\*\*

\- \*\*Open Market portals\*\*

\- \*\*Google Custom Search Engine (CSE)\*\*

\- (Optional) BidPrime API



\## Features

\- Automatic keyword + category classification

\- SQLite storage + schema migrations

\- Duplicate detection

\- Background scheduler (Windows Task Scheduler)

\- Configurable via JSON (`keywords.json`, `naics.json`)



\## Quickstart

```bash

git clone https://github.com/manleysolutions/BisSense\_FINAL.git

cd BidSense\_Final

pip install -r requirements.txt

python fetch\_all.py --days 30 --limit 50

python check\_db.py



