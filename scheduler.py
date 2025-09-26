import schedule
import time
import subprocess
import datetime

def run_fetch():
    """Run the fetch_all.py script with preset args."""
    print(f"[{datetime.datetime.now()}] Starting scheduled fetch...")
    try:
        subprocess.run(
            ["python", "fetch_all.py", "--days", "30", "--limit", "50"],
            check=True
        )
        print(f"[{datetime.datetime.now()}] ✅ Fetch complete.")
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.datetime.now()}] ❌ Fetch failed: {e}")

def main():
    # Run once immediately on startup
    run_fetch()

    # Schedule: every 6 hours (you can adjust to daily, hourly, etc.)
    schedule.every(6).hours.do(run_fetch)

    print("📅 Scheduler started. Running fetch every 6 hours...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # check every minute

if __name__ == "__main__":
    main()
