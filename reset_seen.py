# reset_seen.py
"""
Utility to clear deduplication memory (seen_hashes).
This allows fetch_all.py to re-insert results for testing/debugging.
"""

import os
import pickle

DEDUP_FILE = "seen_hashes.pkl"

def main():
    if os.path.exists(DEDUP_FILE):
        os.remove(DEDUP_FILE)
        print(f"✅ Deduplication cache cleared: {DEDUP_FILE}")
    else:
        print("ℹ️ No deduplication cache found.")

if __name__ == "__main__":
    main()
