from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json, time, os, logging
from typing import List, Dict

# Import bots
from university_bots.stellenbosch_bot import Applicant as StellApplicant, StellenboschBot
from university_bots.up_bot import Applicant as UPApplicant, UPBot
from university_bots.wits_bot import Applicant as WitsApplicant, WitsBot

logger = logging.getLogger("orchestrator_parallel")
logging.basicConfig(level=os.getenv("BOT_LOG_LEVEL", "INFO"))

ARTIFACT_DIR = Path(os.getenv("ARTIFACT_DIR", "artifacts"))
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def _run_bot(bot_name: str, payload: Dict) -> Dict:
    try:
        if bot_name == "stellenbosch":
            app = StellApplicant(**payload)
            bot = StellenboschBot(app)
        elif bot_name == "up":
            app = UPApplicant(**payload)
            bot = UPBot(app)
        elif bot_name == "wits":
            app = WitsApplicant(**payload)
            bot = WitsBot(app)
        else:
            raise ValueError(f"Unknown bot: {bot_name}")
        res = bot.run()
        return {"bot": bot_name, "result": res.__dict__}
    except Exception as e:
        logger.exception("Bot %s failed: %s", bot_name, e)
        return {"bot": bot_name, "error": str(e)}


def run_parallel_bots(applicant_payload: Dict, bots: List[str] = None, max_workers: int = 3) -> Dict:
    """Run selected university bots in parallel threads.
    applicant_payload must satisfy Applicant schema used by each bot.
    """
    bots = bots or ["stellenbosch", "up", "wits"]
    start = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_run_bot, b, applicant_payload): b for b in bots}
        for fut in as_completed(futures):
            results.append(fut.result())
    out = {"started_at": start, "ended_at": time.time(), "results": results}
    (ARTIFACT_DIR / f"parallel_run_{int(time.time())}.json").write_text(json.dumps(out, indent=2))
    return out
