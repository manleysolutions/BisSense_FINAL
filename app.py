import os
import sqlite3
import re
import docx
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecret"

DB_FILE = "opportunities.db"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"pdf", "docx"}

# --------------------------
# File Check Helper
# --------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --------------------------
# Database Utilities
# --------------------------
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            agency TEXT,
            source TEXT,
            issue_date TEXT,
            due_date TEXT,
            url TEXT,
            category TEXT,
            budget REAL,
            status TEXT DEFAULT 'Open'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opp_id INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS corrections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opp_id INTEGER,
            field TEXT,
            parsed_value TEXT,
            corrected_value TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    new_cols_opps = [
        ("contacts", "TEXT"),
        ("submission_method", "TEXT"),
        ("qna_deadline", "TEXT"),
        ("prebid", "TEXT"),
        ("prebid_required", "TEXT"),
        ("set_aside", "TEXT"),
        ("bonding", "TEXT"),
        ("insurance", "TEXT"),
        ("scope_summary", "TEXT"),
        ("tech_requirements", "TEXT"),
        ("external_id", "TEXT")
    ]
    for col, col_type in new_cols_opps:
        try:
            cur.execute(f"ALTER TABLE opportunities ADD COLUMN {col} {col_type}")
            print(f"✅ Added missing column: {col}")
        except sqlite3.OperationalError:
            pass

    try:
        cur.execute("ALTER TABLE scores ADD COLUMN score INTEGER")
        print("✅ Added missing column: score")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

# --------------------------
# Ingestion
# --------------------------
def ingest_opportunity(item, score=None):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO opportunities 
        (title, agency, source, issue_date, due_date, url, category, budget, status,
         contacts, submission_method, qna_deadline, prebid, prebid_required, set_aside,
         bonding, insurance, scope_summary, tech_requirements, external_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item.get("title"),
        item.get("agency"),
        item.get("source"),
        item.get("issue_date"),
        item.get("due_date"),
        item.get("url"),
        item.get("category"),
        item.get("budget"),
        item.get("status", "Open"),
        item.get("contacts"),
        item.get("submission_method"),
        item.get("qna_deadline"),
        item.get("prebid"),
        item.get("prebid_required"),
        item.get("set_aside"),
        item.get("bonding"),
        item.get("insurance"),
        item.get("scope_summary"),
        item.get("tech_requirements"),
        item.get("external_id")
    ))
    opp_id = cur.lastrowid

    if score is not None:
        cur.execute("INSERT INTO scores (opp_id, score) VALUES (?, ?)", (opp_id, score))

    conn.commit()
    conn.close()
    return opp_id

def log_corrections(opp_id, parsed, corrected):
    conn = get_db()
    cur = conn.cursor()
    for field, parsed_val in parsed.items():
        corr_val = corrected.get(field)
        if str(parsed_val) != str(corr_val):
            cur.execute("""
                INSERT INTO corrections (opp_id, field, parsed_value, corrected_value)
                VALUES (?, ?, ?, ?)
            """, (opp_id, field, str(parsed_val), str(corr_val)))
    conn.commit()
    conn.close()

# --------------------------
# Helpers for Parsing
# --------------------------
def _extract_text(filepath):
    text = ""
    try:
        if filepath.lower().endswith(".docx"):
            d = docx.Document(filepath)
            text = "\n".join(p.text for p in d.paragraphs)
        elif filepath.lower().endswith(".pdf"):
            try:
                import PyPDF2
                with open(filepath, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    pages = [pg.extract_text() or "" for pg in reader.pages]
                    text = "\n".join(pages)
            except Exception:
                with open(filepath, "rb") as f:
                    text = f.read().decode(errors="ignore")
        else:
            with open(filepath, "rb") as f:
                text = f.read().decode(errors="ignore")
    except Exception:
        text = ""
    text = re.sub(r"[ \t]+", " ", text)
    return text

def _find(patterns, text, flags=re.I):
    for pat in patterns:
        m = re.search(pat, text, flags)
        if m:
            return (m.group(m.lastindex) or m.group(0)).strip()
    return ""

def _bool_search(patterns, text, flags=re.I):
    return any(re.search(p, text, flags) for p in patterns)

def _safe_money(text):
    m = re.search(r"\$\s*([\d,]+(?:\.\d{2})?)", text)
    if m:
        try: return float(m.group(1).replace(",", ""))
        except: return None
    return None

def _classify_category(text):
    t = text.lower()
    if re.search(r"\b(das|distributed antenna|neutral[- ]host)\b", t): return "DAS / In-Building Cellular"
    if re.search(r"\b(pots[- ]?in[- ]a[- ]box|pots replacement|analog line|fxs|ata)\b", t): return "POTS Replacement / Analog Modernization"
    if re.search(r"\b(voip|hosted voip|phone system|pbx|teams voice|sip trunk)\b", t): return "VoIP / Telephony"
    if re.search(r"\b(cctv|video surveillance|camera system|alpr|license plate)\b", t): return "CCTV / Camera / ALPR"
    if re.search(r"\b(server|compute|poweredge|storage array)\b", t): return "Server / Compute"
    if re.search(r"\b(wifi|wireless|access point|lan|network)\b", t): return "Network / Wireless"
    return "Uploaded RFP"

def _join_unique(parts):
    return " | ".join(dict.fromkeys([p.strip() for p in parts if p and p.strip()]))

# --------------------------
# Parser
# --------------------------
def parse_rfp(filepath):
    text = _extract_text(filepath)
    lower = text.lower()
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

    external_id = _find([
        r"\b(RFP[- ]?\w+)\b",
        r"\b(RFQ[- ]?\w+)\b",
        r"\b(RFB[- ]?\w+)\b",
        r"\b(ITB[- ]?\w+)\b",
        r"\b(CC[#\- ]\s*\d{2}[- ]\d{2,})\b",
        r"\b(\d{5}25R\d{4,})\b",
        r"\b(W\d{4,}[A-Z0-9]+)\b"
    ], text)

    title = "Uploaded RFP"
    head = " ".join(lines[:40])
    t_match = re.search(r"(RFP|RFB|RFQ|ITB).{0,8}[:\-–]?\s*(.{8,120})", head, re.I)
    if t_match:
        title = t_match.group(0).strip()
    elif external_id:
        title = external_id

    agency = _find([
        r"\b(City of [A-Z][A-Za-z .'-]+)\b",
        r"\b(County of [A-Z][A-Za-z .'-]+)\b",
        r"\b(Borough of [A-Z][A-Za-z .'-]+)\b",
        r"\b(University of [A-Z][A-Za-z .'-]+)\b",
        r"\b([A-Z][A-Za-z .'-]+ University)\b",
        r"\b(Department of the Air Force|U\.?S\.? Air Force)\b",
        r"\b(U\.?S\.? Holocaust Memorial Museum)\b",
        r"\b(Housing Authority)\b"
    ], text) or "Unknown Agency"

    issue_date = _find([r"Issue(?:d)? Date[: ]+(.+)"], text)
    due_date = _find([r"(Due Date|Closing Date|Proposals Due)[: ]+(.+)"], text)
    qna_deadline = _find([r"(Q&A Deadline|Questions Due)[: ]+(.+)"], text)

    submission_method = "Not Specified"
    if "bidnet" in lower: submission_method = "BidNet"
    elif "planetbids" in lower: submission_method = "PlanetBids"
    elif "demandstar" in lower: submission_method = "DemandStar"
    elif "sam.gov" in lower: submission_method = "SAM.gov"
    elif "email" in lower: submission_method = "Email"
    elif "portal" in lower: submission_method = "Portal"
    elif "hand delivery" in lower or "sealed bid" in lower: submission_method = "Physical"

    prebid = _find([r"(Pre[- ]bid.*)"], text)
    prebid_required = "Mandatory" if "mandatory" in lower and prebid else ("Optional" if prebid else "N/A")

    set_aside = _find([r"(8[ -]?a|WOSB|SDVOSB|Small Business Set[- ]Aside)"], text) or "None"
    bonding = "Required" if _bool_search([r"bid bond", r"performance bond"], lower) else "Not Mentioned"
    insurance = "Required" if "insurance" in lower else "Not Mentioned"

    budget = _safe_money(text)

    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phones = re.findall(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    poc_name = ""
    if emails:
        for ln in lines:
            if emails[0] in ln:
                nm = re.findall(r"\b[A-Z][a-z]+(?: [A-Z][a-z]+){0,2}\b", ln)
                poc_name = " ".join(nm[:2]) if nm else ""
                break
    contacts = _join_unique([poc_name, (emails[0] if emails else ""), (phones[0] if phones else "")])

    scope = _find([r"(Scope of Work|Project Description)[:\n]\s*(.{50,600})"], text, re.I | re.S) or "Not parsed"

    tech_requirements = []
    if "das" in lower: tech_requirements.append("DAS / Neutral Host")
    if "pots" in lower or "analog line" in lower: tech_requirements.append("POTS Replacement")
    if "voip" in lower or "pbx" in lower: tech_requirements.append("VoIP")
    if "cctv" in lower or "camera" in lower or "alpr" in lower: tech_requirements.append("CCTV/Camera/ALPR")
    if "wifi" in lower or "wireless" in lower: tech_requirements.append("Wireless / Wi-Fi")
    if "server" in lower or "poweredge" in lower: tech_requirements.append("Server / Compute")
    tech_requirements = ", ".join(dict.fromkeys(tech_requirements)) if tech_requirements else "Not parsed"

    category = _classify_category(text)

    parsed = {
        "title": title,
        "agency": agency,
        "source": "Manual Upload",
        "issue_date": issue_date,
        "due_date": due_date,
        "url": "",
        "category": category,
        "budget": budget,
        "contacts": contacts,
        "submission_method": submission_method,
        "qna_deadline": qna_deadline,
        "prebid": prebid,
        "prebid_required": prebid_required,
        "set_aside": set_aside,
        "bonding": bonding,
        "insurance": insurance,
        "scope_summary": scope,
        "tech_requirements": tech_requirements,
        "external_id": external_id or None
    }
    return parsed

# --------------------------
# Mode Handling
# --------------------------
@app.before_request
def set_mode():
    if "training_mode" not in session:
        session["training_mode"] = True

@app.route("/toggle_mode")
def toggle_mode():
    session["training_mode"] = not session.get("training_mode", True)
    return redirect(url_for("index"))

# --------------------------
# Routes
# --------------------------
@app.route("/")
def index():
    status_filter = request.args.get("status")
    conn = get_db()
    cur = conn.cursor()
    if status_filter:
        cur.execute("""
            SELECT o.*, s.score
            FROM opportunities o
            LEFT JOIN scores s ON o.id = s.opp_id
            WHERE o.status=?
            ORDER BY o.due_date ASC
        """, (status_filter,))
    else:
        cur.execute("""
            SELECT o.*, s.score
            FROM opportunities o
            LEFT JOIN scores s ON o.id = s.opp_id
            ORDER BY o.due_date ASC
        """)
    opportunities = cur.fetchall()
    conn.close()
    return render_template("index.html", opportunities=opportunities)

@app.route("/upload", methods=["GET","POST"])
def upload_rfp():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            return "No file selected", 400
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            parsed = parse_rfp(filepath)
            if session.get("training_mode", True):
                session["parsed_rfp"] = parsed
                return render_template("review.html", data=parsed)
            else:
                ingest_opportunity(parsed, score=75)
                return redirect(url_for("index"))
    return render_template("upload.html")

@app.route("/review", methods=["POST"])
def review_rfp():
    parsed = session.get("parsed_rfp", {})
    corrected = {k: request.form.get(k, "") for k in parsed.keys()}
    opp_id = ingest_opportunity(corrected, score=75)
    log_corrections(opp_id, parsed, corrected)
    return redirect(url_for("index"))

@app.route("/update_status/<int:opp_id>/<status>")
def update_status(opp_id, status):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE opportunities SET status=? WHERE id=?", (status, opp_id))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/delete/<int:opp_id>")
def delete_opportunity(opp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM opportunities WHERE id=?", (opp_id,))
    cur.execute("DELETE FROM scores WHERE opp_id=?", (opp_id,))
    cur.execute("DELETE FROM corrections WHERE opp_id=?", (opp_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# --------------------------
# Startup
# --------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
