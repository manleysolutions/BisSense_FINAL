import os
import re
import json
import mimetypes
import sqlite3
import shutil
import requests
import docx
from flask import (
    Flask, render_template, request, redirect, url_for, session,
    send_file, abort
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecret"  # replace in production

DB_FILE = "opportunities.db"

# Writable locally & on Render
BASE_UPLOAD = "/tmp/uploads"
os.makedirs(BASE_UPLOAD, exist_ok=True)
app.config["UPLOAD_FOLDER"] = BASE_UPLOAD
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024  # 64 MB

ALLOWED_EXTENSIONS = {
    "pdf", "doc", "docx", "xls", "xlsx", "csv", "txt", "png", "jpg", "jpeg", "gif"
}

TRAINING_FILE = "rfp_training.jsonl"


# --------------------------
# Helpers
# --------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_opp_dir(opp_id: int) -> str:
    folder = os.path.join(BASE_UPLOAD, f"opp_{opp_id}")
    os.makedirs(folder, exist_ok=True)
    return folder


# --------------------------
# DB init + seed
# --------------------------
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
            status TEXT DEFAULT 'Open',
            contacts TEXT,
            submission_method TEXT,
            qna_deadline TEXT,
            prebid TEXT,
            prebid_required TEXT,
            set_aside TEXT,
            bonding TEXT,
            insurance TEXT,
            scope_summary TEXT,
            tech_requirements TEXT,
            external_id TEXT,
            -- Phase 3.1 engineering fields
            system_type TEXT,
            coverage_goal TEXT,
            vendor TEXT,
            distributor TEXT,
            area_sqft REAL,
            rf_notes TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opp_id INTEGER,
            score INTEGER
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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opp_id INTEGER,
            stored_path TEXT,
            original_name TEXT,
            mime TEXT,
            size INTEGER,
            source_url TEXT,
            note TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Safe migrations
    for col, ctype in [
        ("system_type", "TEXT"),
        ("coverage_goal", "TEXT"),
        ("vendor", "TEXT"),
        ("distributor", "TEXT"),
        ("area_sqft", "REAL"),
        ("rf_notes", "TEXT"),
    ]:
        try:
            cur.execute(f"ALTER TABLE opportunities ADD COLUMN {col} {ctype}")
        except sqlite3.OperationalError:
            pass
    try:
        cur.execute("ALTER TABLE scores ADD COLUMN score INTEGER")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


def seed_training():
    if not os.path.exists(TRAINING_FILE):
        return
    conn = get_db()
    cur = conn.cursor()
    with open(TRAINING_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except Exception:
                continue
            ext_id = item.get("id")
            if not ext_id:
                continue
            cur.execute("SELECT 1 FROM opportunities WHERE external_id=?", (ext_id,))
            if cur.fetchone():
                continue

            tech = item.get("tech_requirements")
            tech_str = ", ".join(tech) if isinstance(tech, list) else (tech or "")

            cur.execute("""
                INSERT INTO opportunities
                (title, agency, source, issue_date, due_date, url, category, budget, status,
                 contacts, submission_method, qna_deadline, prebid, prebid_required,
                 set_aside, bonding, insurance, scope_summary, tech_requirements, external_id,
                 system_type, coverage_goal, vendor, distributor, area_sqft, rf_notes)
                VALUES (?, ?, 'Training Dataset', ?, ?, '', ?, ?, 'Open',
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                        NULL, NULL, NULL, NULL, NULL, NULL)
            """, (
                item.get("title"), item.get("agency"),
                item.get("issue_date"), item.get("due_date"),
                item.get("category"), item.get("budget"),
                item.get("contacts"), item.get("submission_method"),
                item.get("qna_deadline"), item.get("prebid"), item.get("prebid_required"),
                item.get("set_aside"), item.get("bonding"), item.get("insurance"),
                item.get("scope_summary"), tech_str, ext_id
            ))
            opp_id = cur.lastrowid
            ev = item.get("evaluation_factors")
            if isinstance(ev, dict):
                score = sum(v for v in ev.values() if isinstance(v, (int, float)))
                cur.execute("INSERT INTO scores (opp_id, score) VALUES (?, ?)", (opp_id, int(score)))
    conn.commit()
    conn.close()


# --------------------------
# Parsing
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
                    pages = []
                    for pg in reader.pages:
                        try:
                            pages.append(pg.extract_text() or "")
                        except Exception:
                            pages.append("")
                    text = "\n".join(pages)
            except Exception as e:
                print(f"⚠️ PyPDF2 failed: {e}")
                try:
                    from pdfminer.high_level import extract_text
                    text = extract_text(filepath)
                except Exception as e2:
                    print(f"⚠️ pdfminer also failed: {e2}")
        else:
            with open(filepath, "rb") as f:
                text = f.read().decode(errors="ignore")
    except Exception as e:
        print(f"⚠️ Extraction error: {e}")

    text = (text or "").replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = text.replace("\r", "")
    return text


def _find(patterns, text, flags=re.I):
    for pat in patterns:
        m = re.search(pat, text, flags)
        if m:
            try:
                return (m.group(m.lastindex) or m.group(0)).strip()
            except Exception:
                return m.group(0).strip()
    return ""


def _money(text):
    m = re.search(r"\$\s*([\d,]+(?:\.\d{2})?)", text)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except Exception:
            return None
    return None


def _category(text):
    t = (text or "").lower()
    if re.search(r"\b(das|distributed antenna|neutral[- ]host)\b", t): return "DAS / In-Building Cellular"
    if re.search(r"\b(pots[- ]?in[- ]a[- ]box|pots replacement|analog line|fxs|ata)\b", t): return "POTS Replacement / Analog Modernization"
    if re.search(r"\b(voip|pbx|sip|teams voice)\b", t): return "VoIP / Telephony"
    if re.search(r"\b(cctv|video surveillance|camera|alpr)\b", t): return "CCTV / Camera / ALPR"
    if re.search(r"\b(server|compute|storage|poweredge)\b", t): return "Server / Compute"
    if re.search(r"\b(wifi|wireless|lan|access point)\b", t): return "Network / Wireless"
    return "Uploaded RFP"


def parse_rfp(filepath):
    text = _extract_text(filepath)
    if not text:
        return {
            "title": os.path.basename(filepath),
            "agency": "Unknown Agency",
            "source": "Manual Upload",
            "issue_date": "", "due_date": "", "url": "",
            "category": "Uploaded RFP", "budget": None, "contacts": "",
            "submission_method": "Not Specified", "qna_deadline": "",
            "prebid": "", "prebid_required": "N/A", "set_aside": "None",
            "bonding": "Not Mentioned", "insurance": "Not Mentioned",
            "scope_summary": "Not parsed", "tech_requirements": "Not parsed",
            "external_id": None
        }

    lower = text.lower()
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

    external_id = _find([
        r"(RFP[- ]?\d[\w\-./#]*)", r"(RFQ[- ]?\d[\w\-./#]*)", r"(RFB[- ]?\d[\w\-./#]*)",
        r"(ITB[- ]?\d[\w\-./#]*)", r"(BPA[- ]?\d[\w\-./#]*)",
        r"(CC[#\- ]\d{2,}[- ]\d+)", r"(\d{5}25R\d+)", r"(W\d{4,}[A-Z0-9]+)"
    ], text)

    title = _find([r"(RFP|RFB|RFQ|ITB).{0,12}[:\- ]?\s*(.{6,140})"], text, re.I)
    if not title:
        title = lines[0][:120] if lines else "Uploaded RFP"

    agency = _find([
        r"(City of [A-Z][A-Za-z .'-]+)", r"(County of [A-Z][A-Za-z .'-]+)",
        r"(Borough of [A-Z][A-Za-z .'-]+)", r"(University of [A-Z][A-Za-z .'-]+)",
        r"([A-Z][A-Za-z .'-]+ University)", r"(School District of [A-Z][A-Za-z .'-]+)",
        r"(Department of [A-Z][A-Za-z .'-]+)", r"([A-Z][A-Za-z .'-]+ Authority)",
        r"(U\.?S\.? [A-Z][A-Za-z .'-]+)"
    ], text) or "Unknown Agency"

    date_pat = r"(\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|[A-Za-z]{3,9}\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2})\b)"
    issue_date = _find([r"Issue(?:d)? Date[: ]+" + date_pat, r"Release Date[: ]+" + date_pat], text)
    due_date   = _find([r"(Due Date|Closing Date|Proposals Due|Bid Due)[: ]+" + date_pat], text)
    qna_deadline = _find([r"(Q&A Deadline|Questions Due|Inquiry Deadline)[: ]+" + date_pat], text)

    submission_method = "Not Specified"
    for portal in ["BidNet", "PlanetBids", "DemandStar", "Public Purchase", "SAM.gov", "email", "portal", "sealed bid", "hand delivery"]:
        if portal.lower() in lower:
            submission_method = portal
            break

    prebid = _find([r"(Pre[- ]?(bid|proposal)[^.\n]{0,120})"], text)
    prebid_required = "Mandatory" if ("mandatory" in lower and prebid) else ("Optional" if prebid else "N/A")

    set_aside = _find([r"(8[ -]?a|WOSB|SDVOSB|MBE|WBE|DBE|Small Business Set[- ]Aside)"], text) or "None"
    bonding = "Required" if re.search(r"(bid bond|performance bond|payment bond)", lower) else "Not Mentioned"
    insurance = "Required" if "insurance" in lower else "Not Mentioned"

    budget = _money(text)

    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phones = re.findall(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    contacts = " | ".join(dict.fromkeys(emails + phones)) if (emails or phones) else ""

    scope = _find([r"(Scope of Work|Project Description|Summary)[:\n]\s*(.{80,600})"], text, re.I | re.S) or "Not parsed"

    tech_bits = []
    if "das" in lower or "distributed antenna" in lower or "neutral host" in lower: tech_bits.append("DAS / Neutral Host")
    if "pots" in lower or "analog" in lower or "fxs" in lower or "ata" in lower: tech_bits.append("POTS / Analog")
    if "voip" in lower or "pbx" in lower or "sip" in lower or "teams" in lower: tech_bits.append("VoIP / Telephony")
    if "cctv" in lower or "camera" in lower or "alpr" in lower: tech_bits.append("CCTV/Camera/ALPR")
    if "wifi" in lower or "wireless" in lower or "access point" in lower: tech_bits.append("Wireless / Wi-Fi")
    if "server" in lower or "storage" in lower or "poweredge" in lower: tech_bits.append("Server / Compute")
    tech_requirements = ", ".join(dict.fromkeys(tech_bits)) if tech_bits else "Not parsed"

    category = _category(text)

    return {
        "title": title, "agency": agency, "source": "Manual Upload",
        "issue_date": issue_date, "due_date": due_date, "url": "",
        "category": category, "budget": budget, "contacts": contacts,
        "submission_method": submission_method, "qna_deadline": qna_deadline,
        "prebid": prebid, "prebid_required": prebid_required,
        "set_aside": set_aside, "bonding": bonding, "insurance": insurance,
        "scope_summary": scope, "tech_requirements": tech_requirements,
        "external_id": external_id
    }


# --------------------------
# Insert + corrections
# --------------------------
def ingest_opportunity(item, score=None):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO opportunities
        (title, agency, source, issue_date, due_date, url, category, budget, status,
         contacts, submission_method, qna_deadline, prebid, prebid_required,
         set_aside, bonding, insurance, scope_summary, tech_requirements, external_id,
         system_type, coverage_goal, vendor, distributor, area_sqft, rf_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Open',
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                NULL, NULL, NULL, NULL, NULL, NULL)
    """, (
        item.get("title"), item.get("agency"), item.get("source", "Manual Upload"),
        item.get("issue_date"), item.get("due_date"), item.get("url", ""),
        item.get("category"), item.get("budget"),
        item.get("contacts"), item.get("submission_method"),
        item.get("qna_deadline"), item.get("prebid"), item.get("prebid_required"),
        item.get("set_aside"), item.get("bonding"), item.get("insurance"),
        item.get("scope_summary"), item.get("tech_requirements"),
        item.get("external_id")
    ))
    opp_id = cur.lastrowid
    if score is not None:
        cur.execute("INSERT INTO scores (opp_id, score) VALUES (?, ?)", (opp_id, int(score)))
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
# Mode + routes
# --------------------------
@app.before_request
def set_mode():
    if "training_mode" not in session:
        session["training_mode"] = True

@app.route("/toggle_mode")
def toggle_mode():
    session["training_mode"] = not session.get("training_mode", True)
    return redirect(url_for("index"))

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
            WHERE o.status = ?
            ORDER BY o.due_date ASC
        """, (status_filter,))
    else:
        cur.execute("""
            SELECT o.*, s.score
            FROM opportunities o
            LEFT JOIN scores s ON o.id = s.opp_id
            ORDER BY o.due_date ASC
        """)
    opportunities = [dict(r) for r in cur.fetchall()]
    conn.close()
    return render_template("index.html",
                           opportunities=opportunities,
                           training_mode=session.get("training_mode", True))

# ---------- Upload (file) ----------
@app.route("/upload", methods=["GET", "POST"])
def upload_rfp():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            return "❌ No file selected", 400
        if not allowed_file(file.filename):
            return "❌ Invalid file type", 400

        filename = secure_filename(file.filename)
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        # collision-avoid
        i = 1
        base, ext = os.path.splitext(filename)
        while os.path.exists(path):
            filename = f"{base}_{i}{ext}"
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            i += 1

        file.save(path)
        parsed = parse_rfp(path)

        if session.get("training_mode", True):
            session["parsed_rfp"] = {k: (v if isinstance(v, (str, int, float)) or v is None else str(v)) for k, v in parsed.items()}
            session["pending_attachment"] = {
                "path": path, "original": filename,
                "mime": mimetypes.guess_type(path)[0] or "application/octet-stream",
                "size": os.path.getsize(path),
                "note": "Uploaded file", "source_url": None
            }
            return render_template("review.html", data=session["parsed_rfp"])
        else:
            opp_id = ingest_opportunity(parsed, score=75)
            # attach immediately
            folder = ensure_opp_dir(opp_id)
            dest = os.path.join(folder, filename)
            try:
                shutil.move(path, dest)
            except Exception:
                dest = path  # fallback: keep original path
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO attachments (opp_id, stored_path, original_name, mime, size, source_url, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (opp_id, dest, filename,
                  mimetypes.guess_type(dest)[0] or "application/octet-stream",
                  os.path.getsize(dest), None, "Uploaded file"))
            conn.commit()
            conn.close()
            return redirect(url_for("opportunity_detail", opp_id=opp_id))

    return render_template("upload.html")

# ---------- Upload (URL fetch) ----------
@app.route("/upload_url", methods=["POST"])
def upload_rfp_url():
    url = request.form.get("url", "").strip()
    note = request.form.get("note", "")
    if not url:
        return "❌ URL required", 400

    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()

        cd = r.headers.get("content-disposition", "")
        m = re.search(r'filename="?([^";]+)"?', cd)
        fname = m.group(1) if m else url.split("/")[-1].split("?")[0] or "downloaded_file"
        fname = secure_filename(fname)
        if "." not in fname:
            fname += ".pdf"
        if not allowed_file(fname):
            return "❌ Unsupported file type from URL", 400

        stored = fname
        path = os.path.join(app.config["UPLOAD_FOLDER"], stored)
        i = 1
        name, ext = os.path.splitext(stored)
        while os.path.exists(path):
            stored = f"{name}_{i}{ext}"
            path = os.path.join(app.config["UPLOAD_FOLDER"], stored)
            i += 1

        with open(path, "wb") as f:
            f.write(r.content)

        parsed = parse_rfp(path)

        if session.get("training_mode", True):
            session["parsed_rfp"] = {k: (v if isinstance(v, (str, int, float)) or v is None else str(v)) for k, v in parsed.items()}
            session["pending_attachment"] = {
                "path": path, "original": stored,
                "mime": mimetypes.guess_type(path)[0] or "application/octet-stream",
                "size": os.path.getsize(path), "note": note, "source_url": url
            }
            return render_template("review.html", data=session["parsed_rfp"])
        else:
            opp_id = ingest_opportunity(parsed, score=75)
            folder = ensure_opp_dir(opp_id)
            dest = os.path.join(folder, stored)
            try:
                shutil.move(path, dest)
            except Exception:
                dest = path
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO attachments (opp_id, stored_path, original_name, mime, size, source_url, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (opp_id, dest, stored,
                  mimetypes.guess_type(dest)[0] or "application/octet-stream",
                  os.path.getsize(dest), url, note))
            conn.commit()
            conn.close()
            return redirect(url_for("opportunity_detail", opp_id=opp_id))

    except Exception as e:
        return f"❌ Fetch failed: {e}", 500

# ---------- Review (Training Mode save) ----------
@app.route("/review", methods=["POST"])
def review_rfp():
    parsed = session.get("parsed_rfp", {})
    corrected = {k: request.form.get(k, parsed.get(k, "")) for k in parsed.keys()}
    opp_id = ingest_opportunity(corrected, score=75)
    log_corrections(opp_id, parsed, corrected)

    # Attach pending file (from upload or URL) and move it into opp folder
    att = session.pop("pending_attachment", None)
    if att:
        folder = ensure_opp_dir(opp_id)
        dest = os.path.join(folder, att["original"])
        try:
            shutil.move(att["path"], dest)
        except Exception:
            dest = att["path"]
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO attachments (opp_id, stored_path, original_name, mime, size, source_url, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (opp_id, dest, att["original"], att["mime"], att["size"], att.get("source_url"), att.get("note")))
        conn.commit()
        conn.close()

    return redirect(url_for("opportunity_detail", opp_id=opp_id))

# ---------- Status ----------
@app.route("/update_status/<int:opp_id>/<status>")
def update_status(opp_id, status):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE opportunities SET status=? WHERE id=?", (status, opp_id))
    conn.commit()
    conn.close()
    return redirect(url_for("index", _anchor=f"row-{opp_id}"))

# ---------- Delete ----------
@app.route("/delete/<int:opp_id>")
def delete_opportunity(opp_id):
    # remove attachment files
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT stored_path FROM attachments WHERE opp_id=?", (opp_id,))
    for r in cur.fetchall():
        try:
            if os.path.exists(r["stored_path"]):
                os.remove(r["stored_path"])
        except Exception:
            pass
    cur.execute("DELETE FROM attachments WHERE opp_id=?", (opp_id,))
    cur.execute("DELETE FROM scores WHERE opp_id=?", (opp_id,))
    cur.execute("DELETE FROM corrections WHERE opp_id=?", (opp_id,))
    cur.execute("DELETE FROM opportunities WHERE id=?", (opp_id,))
    conn.commit()
    conn.close()
    # remove opp folder
    try:
        shutil.rmtree(ensure_opp_dir(opp_id))
    except Exception:
        pass
    return redirect(url_for("index"))

# ---------- Detail + edit ----------
def _get_opportunity(opp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT o.*, s.score FROM opportunities o LEFT JOIN scores s ON o.id = s.opp_id WHERE o.id=?", (opp_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def _list_attachments(opp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM attachments WHERE opp_id=? ORDER BY created_at DESC", (opp_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.route("/opportunity/<int:opp_id>")
def opportunity_detail(opp_id):
    opp = _get_opportunity(opp_id)
    if not opp:
        abort(404)
    atts = _list_attachments(opp_id)
    if not opp.get("system_type") and ("public safety" in (opp.get("category","").lower())):
        opp["system_type"] = "Public Safety DAS"
    return render_template("opportunity.html", o=opp, attachments=atts)

@app.route("/opportunity/<int:opp_id>/update", methods=["POST"])
def opportunity_update(opp_id):
    fields = ["system_type","coverage_goal","vendor","distributor","area_sqft","rf_notes","url","scope_summary"]
    values = [request.form.get(f) for f in fields]
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"""
        UPDATE opportunities
        SET system_type=?, coverage_goal=?, vendor=?, distributor=?, area_sqft=?, rf_notes=?, url=?, scope_summary=?
        WHERE id=?
    """, (*values, opp_id))
    conn.commit()
    conn.close()
    return redirect(url_for("opportunity_detail", opp_id=opp_id))

# ---------- Attachments (to existing opp) ----------
@app.route("/opportunity/<int:opp_id>/attach", methods=["POST"])
def opportunity_attach(opp_id):
    f = request.files.get("file")
    note = request.form.get("note","")
    if not f or f.filename == "":
        return "❌ No file selected", 400
    if not allowed_file(f.filename):
        return "❌ Invalid file type", 400

    folder = ensure_opp_dir(opp_id)
    original = secure_filename(f.filename)
    stored = original
    i = 1
    while os.path.exists(os.path.join(folder, stored)):
        name, ext = os.path.splitext(original)
        stored = f"{name}_{i}{ext}"
        i += 1
    path = os.path.join(folder, stored)
    f.save(path)

    size = os.path.getsize(path)
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO attachments (opp_id, stored_path, original_name, mime, size, source_url, note)
        VALUES (?, ?, ?, ?, ?, NULL, ?)
    """, (opp_id, path, original, mime, size, note))
    conn.commit()
    conn.close()
    return redirect(url_for("opportunity_detail", opp_id=opp_id))

@app.route("/opportunity/<int:opp_id>/attach_url", methods=["POST"])
def opportunity_attach_url(opp_id):
    url = request.form.get("url","").strip()
    note = request.form.get("note","")
    if not url:
        return "❌ URL required", 400
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        cd = r.headers.get("content-disposition","")
        m = re.search(r'filename="?([^";]+)"?', cd)
        fname = m.group(1) if m else url.split("/")[-1].split("?")[0] or "downloaded_file"
        fname = secure_filename(fname)
        if "." not in fname:
            fname += ".pdf"
        if not allowed_file(fname):
            return "❌ Unsupported file type from URL", 400

        folder = ensure_opp_dir(opp_id)
        stored = fname
        i = 1
        path = os.path.join(folder, stored)
        while os.path.exists(path):
            name, ext = os.path.splitext(fname)
            stored = f"{name}_{i}{ext}"
            path = os.path.join(folder, stored)
            i += 1

        with open(path, "wb") as f:
            f.write(r.content)

        size = os.path.getsize(path)
        mime = mimetypes.guess_type(path)[0] or "application/octet-stream"

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO attachments (opp_id, stored_path, original_name, mime, size, source_url, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (opp_id, path, stored, mime, size, url, note))
        conn.commit()
        conn.close()
        return redirect(url_for("opportunity_detail", opp_id=opp_id))
    except Exception as e:
        return f"❌ Download failed: {e}", 500

@app.route("/attachment/<int:att_id>/download")
def attachment_download(att_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM attachments WHERE id=?", (att_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        abort(404)
    row = dict(row)
    if not os.path.exists(row["stored_path"]):
        abort(404)
    return send_file(row["stored_path"], as_attachment=True, download_name=row["original_name"])

@app.route("/attachment/<int:att_id>/delete")
def attachment_delete(att_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT opp_id, stored_path FROM attachments WHERE id=?", (att_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        abort(404)
    opp_id = row["opp_id"]
    path = row["stored_path"]
    cur.execute("DELETE FROM attachments WHERE id=?", (att_id,))
    conn.commit()
    conn.close()
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
    return redirect(url_for("opportunity_detail", opp_id=opp_id))


# --------------------------
# Startup
# --------------------------
if __name__ == "__main__":
    init_db()
    seed_training()
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
