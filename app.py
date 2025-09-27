import os
import sqlite3
import json
from flask import Flask, render_template, jsonify, Response, send_file
from io import BytesIO
import csv
from openpyxl import Workbook

app = Flask(__name__)
DB_FILE = "opportunities.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.id, o.title, o.agency, o.source, o.issue_date, o.due_date,
               o.url, o.category,
               s.score, a.decision, a.reason, s.breakdown
        FROM opportunities o
        LEFT JOIN scores s ON o.id = s.opportunity_id
        LEFT JOIN approvals a ON o.id = a.opportunity_id
        ORDER BY o.id DESC
    """)
    opportunities = cur.fetchall()
    conn.close()
    return render_template("index.html", opportunities=opportunities)

@app.route("/breakdown/<int:opp_id>")
def breakdown(opp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT breakdown FROM scores WHERE opportunity_id=?", (opp_id,))
    row = cur.fetchone()
    conn.close()

    if not row or not row["breakdown"]:
        return jsonify({"error": "No breakdown available"}), 404

    try:
        data = json.loads(row["breakdown"])
    except Exception:
        return jsonify({"error": "Invalid breakdown JSON"}), 500

    return jsonify(data)

@app.route("/export/csv")
def export_csv():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.id, o.title, o.agency, o.category, o.due_date,
               s.score, a.decision, a.reason, s.breakdown
        FROM opportunities o
        LEFT JOIN scores s ON o.id = s.opportunity_id
        LEFT JOIN approvals a ON o.id = a.opportunity_id
        ORDER BY o.id DESC
    """)
    rows = cur.fetchall()
    conn.close()

    output = []
    headers = [
        "ID","Title","Agency","Category","Due Date",
        "Score","Approval","Reason",
        "Is Core","Is Strategic","Days Until Due",
        "Profit Revenue","Profit Cost","Profit Margin %","Profit Note",
        "Component Breakdown"
    ]
    output.append(headers)

    for r in rows:
        bd = {}
        try:
            bd = json.loads(r["breakdown"]) if r["breakdown"] else {}
        except:
            bd = {}

        flags = bd.get("flags", {})
        profit = bd.get("profit_estimate", {})
        comps = bd.get("components", [])

        output.append([
            r["id"], r["title"], r["agency"], r["category"], r["due_date"],
            r["score"], r["decision"], r["reason"],
            flags.get("is_core"), flags.get("is_strategic"), flags.get("days_until_due"),
            profit.get("revenue"), profit.get("cost"),
            round(profit.get("margin_ratio", 0) * 100, 2) if profit.get("margin_ratio") else None,
            profit.get("note"),
            "; ".join([f"{c[0]}:{c[1]}" for c in comps]) if comps else ""
        ])

    def generate():
        si = BytesIO()
        cw = csv.writer(si)
        cw.writerows(output)
        return si.getvalue()

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=bidsense_export.csv"}
    )

@app.route("/export/excel")
def export_excel():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.id, o.title, o.agency, o.category, o.due_date,
               s.score, a.decision, a.reason, s.breakdown
        FROM opportunities o
        LEFT JOIN scores s ON o.id = s.opportunity_id
        LEFT JOIN approvals a ON o.id = a.opportunity_id
        ORDER BY o.id DESC
    """)
    rows = cur.fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "BidSense Export"

    headers = [
        "ID","Title","Agency","Category","Due Date",
        "Score","Approval","Reason",
        "Is Core","Is Strategic","Days Until Due",
        "Profit Revenue","Profit Cost","Profit Margin %","Profit Note",
        "Component Breakdown"
    ]
    ws.append(headers)

    for r in rows:
        bd = {}
        try:
            bd = json.loads(r["breakdown"]) if r["breakdown"] else {}
        except:
            bd = {}

        flags = bd.get("flags", {})
        profit = bd.get("profit_estimate", {})
        comps = bd.get("components", [])

        ws.append([
            r["id"], r["title"], r["agency"], r["category"], r["due_date"],
            r["score"], r["decision"], r["reason"],
            flags.get("is_core"), flags.get("is_strategic"), flags.get("days_until_due"),
            profit.get("revenue"), profit.get("cost"),
            round(profit.get("margin_ratio", 0) * 100, 2) if profit.get("margin_ratio") else None,
            profit.get("note"),
            "; ".join([f"{c[0]}:{c[1]}" for c in comps]) if comps else ""
        ])

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)

    return send_file(
        bio,
        as_attachment=True,
        download_name="bidsense_export.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    app.run(debug=True)
