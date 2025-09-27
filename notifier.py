# notifier.py
import os
import requests

def _env_bool(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")

# ---- EMAIL (SMTP) -----------------------------------------------------------
import smtplib
from email.mime.text import MIMEText

def send_email(subject: str, body: str) -> bool:
    if not _env_bool("ENABLE_EMAIL", "false"):
        return False

    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    pwd  = os.environ.get("SMTP_PASS")
    from_addr = os.environ.get("ALERT_EMAIL_FROM")
    to_addr   = os.environ.get("ALERT_EMAIL_TO")

    if not all([host, user, pwd, from_addr, to_addr]):
        return False

    try:
        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr

        with smtplib.SMTP(host, port) as s:
            s.starttls()
            s.login(user, pwd)
            s.sendmail(from_addr, [to_addr], msg.as_string())
        return True
    except Exception:
        return False

# ---- SMS (Telnyx only) ------------------------------------------------------
def send_sms(message: str) -> bool:
    if not _env_bool("ENABLE_SMS", "false"):
        return False

    tel_api = os.environ.get("TELNYX_API_KEY")
    tel_from = os.environ.get("TELNYX_FROM")
    sms_to   = os.environ.get("ALERT_SMS_TO")

    if not (tel_api and tel_from and sms_to):
        return False

    try:
        r = requests.post(
            "https://api.telnyx.com/v2/messages",
            headers={"Authorization": f"Bearer {tel_api}"},
            json={"from": tel_from, "to": sms_to, "text": message},
            timeout=15
        )
        return r.ok
    except Exception:
        return False
