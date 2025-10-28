from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json, time, os, logging
from typing import List, Dict
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import smtplib
from email.mime.text import MIMEText
# Import bots
from university_bots.stellenbosch_bot import Applicant as StellApplicant, StellenboschBot
from university_bots.up_bot import Applicant as UPApplicant, UPBot
from university_bots.wits_bot import Applicant as WitsApplicant, WitsBot
# Newly added
from university_bots.uj_bot import run as run_uj
from university_bots.nsfas_bot import run as run_nsfas

logger = logging.getLogger("orchestrator_parallel")
logging.basicConfig(level=os.getenv("BOT_LOG_LEVEL", "INFO"))

ARTIFACT_DIR = Path(os.getenv("ARTIFACT_DIR", "artifacts"))
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

# Google Sheets (optional Supabase) integration via webhook-style appender
GOOGLE_SHEETS_WEBHOOK = os.getenv("GOOGLE_SHEETS_WEBHOOK")  # e.g., Apps Script Web App URL
SUPABASE_WEBHOOK = os.getenv("SUPABASE_WEBHOOK")
DASHBOARD_PUSH_ENABLED = bool(GOOGLE_SHEETS_WEBHOOK or SUPABASE_WEBHOOK)

# Email notifications via Brevo/SMTP
SMTP_HOST = os.getenv("SMTP_HOST", "smtp-relay.brevo.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
ALERT_TO = os.getenv("ALERT_TO")
ALERT_FROM = os.getenv("ALERT_FROM", SMTP_USER or "alerts@ufunda.co.za")

TYPEFORM_SECRET = os.getenv("TYPEFORM_SECRET")  # for signature validation if enabled
WEBHOOK_BIND = os.getenv("WEBHOOK_BIND", "0.0.0.0")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/typeform/submit")


def _send_email(subject: str, body: str):
    if not (SMTP_USER and SMTP_PASS and ALERT_TO):
        logger.info("SMTP not configured; skipping email")
        return
    try:
        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = ALERT_FROM
        msg["To"] = ALERT_TO
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(ALERT_FROM, [ALERT_TO], msg.as_string())
        logger.info("Alert email sent")
    except Exception as e:
        logger.exception("Failed to send email: %s", e)


def _audit(event: str, data: Dict):
    try:
        entry = {
            "ts": time.time(),
            "event": event,
            "data": data,
        }
        (ARTIFACT_DIR / "audit.log").write_text(
            (ARTIFACT_DIR / "audit.log").read_text() + json.dumps(entry) + "\n"
            if (ARTIFACT_DIR / "audit.log").exists() else json.dumps(entry) + "\n"
        )
    except Exception as e:
        logger.exception("Audit write failed: %s", e)


def _push_dashboard(payload: Dict):
    import urllib.request
    import urllib.error
    headers = {"Content-Type": "application/json"}
    body = json.dumps(payload).encode("utf-8")
    for url in filter(None, [GOOGLE_SHEETS_WEBHOOK, SUPABASE_WEBHOOK]):
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                logger.info("Dashboard push %s -> %s", url, resp.status)
        except Exception as e:
            logger.exception("Dashboard push failed for %s: %s", url, e)


def _run_bot(bot_name: str, payload: Dict) -> Dict:
    try:
        if bot_name == "stellenbosch":
            app = StellApplicant(**payload)
            bot = StellenboschBot(app)
            res = bot.run()
            return {"bot": bot_name, "result": res.__dict__}
        elif bot_name == "up":
            app = UPApplicant(**payload)
            bot = UPBot(app)
            res = bot.run()
            return {"bot": bot_name, "result": res.__dict__}
        elif bot_name == "wits":
            app = WitsApplicant(**payload)
            bot = WitsBot(app)
            res = bot.run()
            return {"bot": bot_name, "result": res.__dict__}
        elif bot_name == "uj":
            res = run_uj(driver=None, context=payload)
            return {"bot": bot_name, "result": res}
        elif bot_name == "nsfas":
            res = run_nsfas(driver=None, context=payload)
            return {"bot": bot_name, "result": res}
        else:
            raise ValueError(f"Unknown bot: {bot_name}")
    except Exception as e:
        logger.exception("Bot %s failed: %s", bot_name, e)
        return {"bot": bot_name, "error": str(e)}


def run_parallel_bots(applicant_payload: Dict, bots: List[str] = None, max_workers: int = 5) -> Dict:
    """Run selected university bots in parallel threads and push status to dashboard."""
    bots = bots or ["stellenbosch", "up", "wits", "uj", "nsfas"]
    start = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_run_bot, b, applicant_payload): b for b in bots}
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            # stream push per-bot
            if DASHBOARD_PUSH_ENABLED:
                _push_dashboard({
                    "event": "bot_result",
                    "applicant_ref": applicant_payload.get("id") or applicant_payload.get("email"),
                    "bot": r.get("bot"),
                    "status": "error" if "error" in r else "ok",
                    "result": r.get("result"),
                    "ts": time.time(),
                })
    out = {"started_at": start, "ended_at": time.time(), "results": results}
    (ARTIFACT_DIR / f"parallel_run_{int(time.time())}.json").write_text(json.dumps(out, indent=2))
    if DASHBOARD_PUSH_ENABLED:
        _push_dashboard({
            "event": "run_complete",
            "applicant_ref": applicant_payload.get("id") or applicant_payload.get("email"),
            "summary": out,
        })
    return out


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != WEBHOOK_PATH:
            self.send_response(404); self.end_headers(); self.wfile.write(b"Not found"); return
        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode('utf-8'))
        except Exception:
            payload = {"raw": raw.decode('utf-8', 'ignore')}
        _audit("typeform_webhook_received", {"headers": dict(self.headers), "body": payload})
        # Optionally validate Typeform signature here with TYPEFORM_SECRET
        # Map Typeform fields to applicant schema
        applicant = self._map_typeform_to_applicant(payload)
        # Launch bots in background
        threading.Thread(target=run_parallel_bots, args=(applicant,), daemon=True).start()
        # Immediate response
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "accepted"}).encode('utf-8'))

    def log_message(self, format, *args):
        logger.info("webhook: " + format, *args)

    @staticmethod
    def _map_typeform_to_applicant(tf_payload: Dict) -> Dict:
        # Basic mapping; adjust keys to your Typeform
        answers = {}
        for item in tf_payload.get("form_response", {}).get("answers", []):
            field_id = item.get("field", {}).get("id")
            val = item.get("text") or item.get("email") or item.get("number") or item.get("boolean") or item.get("choices")
            answers[field_id] = val
        email = tf_payload.get("form_response", {}).get("hidden", {}).get("email") or answers.get("email")
        full_name = answers.get("full_name") or tf_payload.get("form_response", {}).get("hidden", {}).get("name")
        applicant = {
            "email": email,
            "full_name": full_name,
            "id": tf_payload.get("event_id") or tf_payload.get("form_response", {}).get("token"),
            # include additional mapped fields used by Applicant models
        }
        return applicant


def run_webhook_server():
    server = HTTPServer((WEBHOOK_BIND, WEBHOOK_PORT), WebhookHandler)
    logger.info("Webhook server listening on %s:%s%s", WEBHOOK_BIND, WEBHOOK_PORT, WEBHOOK_PATH)
    _send_email("Orchestrator started", f"Webhook server on {WEBHOOK_BIND}:{WEBHOOK_PORT}{WEBHOOK_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    mode = os.getenv("MODE", "webhook")
    if mode == "webhook":
        run_webhook_server()
    else:
        # manual test mode
        sample = {"email": "student@example.com", "full_name": "Test User"}
        print(run_parallel_bots(sample))
