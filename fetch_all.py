import argparse
import json
import time
from common import ensure_schema_upgrade, log_event, upsert_opportunity, upsert_cache
from sources.sam_source import SAMSource
from sources.openmarket_source import OpenMarketSource
from sources.bidprime_source import BidPrimeSource
from sources.google_cse_source import GoogleCSESource


def fetch_with_retry(src, days_back, limit, retries=5, backoff_factor=2):
    """Fetch data from a source with retry on failure (like 429)."""
    for attempt in range(retries):
        try:
            return src.fetch(days_back=days_back, limit=limit)
        except Exception as e:
            err = str(e).lower()
            if "429" in err or "too many requests" in err:
                wait = backoff_factor ** attempt
                print(f"⚠️ {src.name} rate limited (429). Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise  # not a rate-limit error, fail fast
    raise Exception(f"{src.name} failed after {retries} retries due to rate limits")


def main():
    parser = argparse.ArgumentParser(description="BidSense Fetch Orchestrator")
    parser.add_argument("--days", type=int, default=7, help="Days back to search")
    parser.add_argument("--limit", type=int, default=50, help="Per-source limit")
    parser.add_argument("--demo", action="store_true", help="Enable demo mode for paid feeds")
    args = parser.parse_args()

    # make sure schema is up to date
    ensure_schema_upgrade()

    # sources enabled
    sources = [
        SAMSource(),
        OpenMarketSource(),
        BidPrimeSource(demo_mode=args.demo),
        GoogleCSESource()
    ]

    totals = {}
    for src in sources:
        name = src.name
        try:
            # ✅ Add retry only for SAM.gov
            if name.lower().startswith("sam"):
                results = fetch_with_retry(src, args.days, args.limit)
            else:
                results = src.fetch(days_back=args.days, limit=args.limit)

            inserted = 0
            for r in results:
                ext_id = upsert_opportunity(r)
                if "raw" in r:
                    upsert_cache(r["source"], ext_id, json.dumps(r["raw"]))
                inserted += 1
            totals[name] = inserted
            log_event("fetch", f"{name}: inserted {inserted}", "success", actor=name)
            print(f"✅ {name}: inserted {inserted}")
        except Exception as e:
            log_event("fetch", f"{name}: {e}", "error", actor=name)
            print(f"❌ {name} fetch error:", e)

    print("=== Summary ===")
    for k, v in totals.items():
        print(f"{k}: {v} inserted")


if __name__ == "__main__":
    main()
