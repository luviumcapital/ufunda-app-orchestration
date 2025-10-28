# Ufunda App Orchestration
## Overview
Automation orchestrator with bots for Gmail account creation and university and bursary applications.

## New Bots Added
- Gmail bot: university_bots/gmail_bot.py (Selenium-based Gmail account creator)
- UCT bot: university_bots/uct_bot.py (Selenium sample for UCT application flow)
- Wits bot: university_bots/wits_bot.py (Wits application automation)
- UP bot: university_bots/up_bot.py (UP application automation)
- Stellenbosch bot: university_bots/stellenbosch_bot.py
- UJ bot: university_bots/uj_bot.py (University of Johannesburg application automation)
- NSFAS bot: university_bots/nsfas_bot.py (NSFAS/SETA bursary automation)

## Quick Start
1) Python 3.10+
2) Install dependencies for university bots:
   pip install -r university_bots/requirements.txt
3) Run orchestrator in parallel across bots (includes uj and nsfas now):
   python -c "from orchestrator.master_orchestrator import run_parallel_bots; import json; print(json.dumps(run_parallel_bots({'first_name':'Test','last_name':'User','email':'test@example.com'}), indent=2))"
4) Run individual bots:
   python -c "from university_bots.uj_bot import run; print(run(None, {'email':'test@example.com'}))"
   python -c "from university_bots.nsfas_bot import run; print(run(None, {'email':'test@example.com'}))"

## Environment Variables (optional)
- General: BOT_LOG_LEVEL, ARTIFACT_DIR
- UJ: provide uj_username, uj_password OR email, id_number, mobile; uploads dict for files; fee_waiver flag
- NSFAS: nsfas_email, nsfas_password OR email, id_number, mobile; uploads dict; otp when required

## Testing and CI
- GitHub Actions: Use Actions tab to run workflows if configured
- Logs: Bots emit structured events consumable by orchestrator; artifacts written to artifacts/ directory

## Notes
- Selectors are placeholders and may need updates as portals change.
- Use headless-safe drivers or provide a Selenium WebDriver via run(driver, context).
