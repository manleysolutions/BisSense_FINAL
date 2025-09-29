import re
from typing import Dict, Optional

DATE_PAT = re.compile(
    r'(?P<label>(issue|posted|release|due|closing|close|site\s*visit|walk[-\s]*through|pre[-\s]*bid|q&a|question)s?)\s*[:\-–]?\s*'
    r'(?P<date>(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4}|\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
    re.IGNORECASE
)

EMAIL_PAT = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+', re.IGNORECASE)
PHONE_PAT = re.compile(r'(\+?1[\s\-\.])?(\(?\d{3}\)?[\s\-\.])\d{3}[\s\-\.]\d{4}')
POC_LINE_PAT = re.compile(r'(contact|point\s*of\s*contact|poc|contracting\s*officer|buyer)\s*[:\-–]', re.IGNORECASE)

LOC_PAT = re.compile(r'(place\s*of\s*performance|location|place\s*of\s*work)\s*[:\-–]?\s*(?P<loc>.+)', re.IGNORECASE)
BUDGET_PAT = re.compile(r'(budget|estimated\s*value|not[-\s]*to[-\s]*exceed|nte)\s*[:\-–]?\s*\$?([\d,]+(\.\d{2})?)', re.IGNORECASE)

SCOPE_HEAD_PAT = re.compile(
    r'(scope\s*of\s*work|statement\s*of\s*work|sow|project\s*scope|background\s*and\s*scope|services\s*required|overview)',
    re.IGNORECASE
)

TERMS_HEAD_PAT = re.compile(
    r'(terms\s*&?\s*conditions|t&c|general\s*conditions|contract\s*terms)',
    re.IGNORECASE
)

CRITICAL_PAT = re.compile(
    r'(mandatory|required|must|shall).{0,60}(site\s*(visit|survey)|pre[-\s]*bid|conference|registration|security\s*clearance|bond|certification)',
    re.IGNORECASE
)

MONEY_CLEAN = re.compile(r'[^\d\.]')

def _first(text: str, pat: re.Pattern) -> Optional[str]:
    m = pat.search(text)
    return m.group(0).strip() if m else None

def _all_dates(text: str) -> Dict[str, str]:
    out = {}
    for m in DATE_PAT.finditer(text):
        label = m.group('label').lower()
        date = m.group('date')
        if 'issue' in label or 'post' in label or 'release' in label:
            out.setdefault('issue_date', date)
        elif 'due' in label or 'clos' in label:
            out.setdefault('due_date', date)
        elif 'site' in label or 'walk' in label or 'pre-bid' in label or 'pre bid' in label:
            out.setdefault('site_visit', date)
        elif 'q' in label:
            out.setdefault('qa_deadline', date)
    return out

def _section_after(head_pat: re.Pattern, text: str, max_chars: int = 2000) -> Optional[str]:
    m = head_pat.search(text)
    if not m:
        return None
    start = m.end()
    chunk = text[start:start+max_chars]
    # stop at next all-caps header or numbered header
    stop = re.search(r'\n[A-Z][A-Z0-9 \-]{6,}\n|^\d+\.\s+[A-Z]', chunk, flags=re.MULTILINE)
    return chunk[:stop.start()].strip() if stop else chunk.strip()

def parse(text: str) -> Dict[str, str]:
    """
    Return a dict with the extracted structured fields.
    """
    text = text.replace('\r', '\n')

    data = {}

    # Dates
    data.update(_all_dates(text))

    # Scope
    scope = _section_after(SCOPE_HEAD_PAT, text, max_chars=4000)
    if not scope:
        # fallback: first 800 chars of body
        scope = text[:800].strip()
    data['scope'] = scope

    # Terms & Conditions
    tnc = _section_after(TERMS_HEAD_PAT, text, max_chars=2500)
    if tnc:
        data['terms'] = tnc

    # POC: try lines with contact header, else just email+phone near each other
    poc = None
    for line in text.splitlines():
        if POC_LINE_PAT.search(line):
            emails = EMAIL_PAT.findall(line)
            phones = PHONE_PAT.findall(line)
            poc = line.strip()
            if emails:
                poc += f" | {', '.join(emails)}"
            if phones:
                # phones is tuples, rebuild strings
                def norm(p): 
                    return re.sub(r'\D','', ''.join(p))
                phones_fmt = ['(' + p[1].strip() + ')' if p[1] else '' for p in phones]
                poc += f" | phones found"
            break
    if not poc:
        # fallback: first email + phone pair we see in the doc
        email = _first(text, EMAIL_PAT)
        phone = _first(text, PHONE_PAT)
        if email or phone:
            poc = " | ".join([x for x in ["Contact", email, phone] if x])
    if poc:
        data['poc'] = poc

    # Location
    mloc = LOC_PAT.search(text)
    if mloc:
        data['location'] = mloc.group('loc').strip()

    # Budget (if published)
    mb = BUDGET_PAT.search(text)
    if mb:
        amt = mb.group(2)
        try:
            data['budget_published'] = float(MONEY_CLEAN.sub('', amt))
        except:
            pass

    # Critical prerequisites
    crits = []
    for m in CRITICAL_PAT.finditer(text):
        crits.append(m.group(0))
    if crits:
        data['critical_reqs'] = " | ".join(sorted(set(crits)))

    return data
