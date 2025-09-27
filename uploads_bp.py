import os
import sqlite3
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

from PyPDF2 import PdfReader
from docx import Document

DB_FILE = "opportunities.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

uploads_bp = Blueprint("uploads_bp", __name__, template_folder="templates")

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

ALLOWED_EXT = {".pdf", ".docx"}

def extract_text_pdf(path):
    text = []
    with open(path, "rb") as f:
        pdf = PdfReader(f)
        for page in pdf.pages:
            try:
                text.append(page.extract_text() or "")
            except Exception:
                pass
    return "\n".join(text).strip()

def extract_text_docx(path):
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs]).strip()

def quick_guess(meta):
    """
    Very light heuristics to guess title/category/budget from extracted text.
    This is intentionally simple; we’ll replace with smarter parsing later.
    """
    text = meta.get("extracted_text", "")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    title = (lines[0][:140] if lines else meta.get("original_name", "Uploaded RFP")).strip()

    # category guess
    category = "General"
    lower = text.lower()
    if "distributed antenna" in lower or "das" in lower: category = "DAS"
    elif "pots" in lower or "centrex" in lower: category = "POTS/Telephony"
    elif "elevator" in lower or "emergency phone" in lower: category = "Elevators/Emergency Phones"
    elif "fire alarm" in lower: category = "Fire Alarm Monitoring"
    elif "5g" in lower or "private network" in lower: category = "5G/Private Networks"
    elif "structured cabling" in lower or "ethernet" in lower or "fiber" in lower: category = "Structured Cabling"
    elif "cybersecurity" in lower or "siem" in lower: category = "Cybersecurity"

    # naive budget grab like "$500,000"
    import re
    budget = 0.0
    m = re.search(r"\$\s?([\d,]+)", text)
    if m:
        try:
            budget = float(m.group(1).replace(",", ""))
        except Exception:
            pass

    return title, category, budget

@uploads_bp.route("/upload", methods=["GET", "POST"])
def upload_rfp():
    if request.method == "POST":
        f = request.files.get("file")
        if not f or f.filename == "":
            flash("Please choose a file.", "warning")
            return redirect(url_for("uploads_bp.upload_rfp"))

        name = secure_filename(f.filename)
        ext = os.path.splitext(name)[1].lower()
        if ext not in ALLOWED_EXT:
            flash("Only PDF and DOCX are supported.", "danger")
            return redirect(url_for("uploads_bp.upload_rfp"))

        path = os.path.join(UPLOAD_DIR, name)
        f.save(path)

        # Extract text
        try:
            if ext == ".pdf":
                text = extract_text_pdf(path)
            else:
                text = extract_text_docx(path)
        except Exception as e:
            text = ""
            flash(f"Parsed with warnings: {e}", "warning")

        # Store upload record
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO rfp_uploads(filename, original_name, mimetype, size_bytes, uploaded_by, uploaded_at, extracted_text)
            VALUES(?,?,?,?,?,?,?)
        """, (name, f.filename, f.mimetype, os.path.getsize(path), None, datetime.utcnow().isoformat(), text))
        upload_id = cur.lastrowid

        # Create an opportunity (best-effort) from extracted text
        title, category, budget = quick_guess({"extracted_text": text, "original_name": f.filename})
        # Minimal agency/dates from text are TBD; leaving blank/soon for now
        issue_date = datetime.utcnow().date().isoformat()
        due_date = None
        url = f"upload://{upload_id}"

        # Unique hash to dedupe
        import hashlib
        opp_hash = hashlib.sha256((title + (url or "")).encode("utf-8")).hexdigest()

        # Ensure opportunities has 'hash' column
        cur.execute("PRAGMA table_info(opportunities)")
        cols = [r[1] for r in cur.fetchall()]
        if "hash" not in cols:
            conn.close()
            flash("Opportunities schema missing 'hash'—run migrate_opportunities_fix.py", "danger")
            return redirect(url_for("uploads_bp.upload_rfp"))

        cur.execute("""
            INSERT OR IGNORE INTO opportunities(title, agency, source, issue_date, due_date, url, category, budget, hash)
            VALUES(?,?,?,?,?,?,?,?,?)
        """, (title, "", "upload", issue_date, due_date, url, category, budget, opp_hash))
        conn.commit()
        conn.close()

        flash("RFP uploaded and parsed. Check the dashboard.", "success")
        return redirect(url_for("index"))

    return render_template("upload.html")
