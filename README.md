# Ufunda App Orchestration

## Overview
Automation orchestrator with bots for Gmail account creation and university applications.

## New Bots Added
- Gmail bot: university_bots/gmail_bot.py (Selenium-based Gmail account creator)
- UCT bot: university_bots/uct_bot.py (Selenium sample for UCT application flow)

## Quick Start
1) Python 3.10+
2) Install dependencies for university bots:
   pip install -r university_bots/requirements.txt
3) Run Gmail bot test:
   python university_bots/gmail_bot.py
4) Run UCT bot sample:
   python university_bots/uct_bot.py

## Environment Variables (optional)
- UCT_PORTAL_URL: Override UCT portal URL (default: https://www.uct.ac.za/apply)
- UCT_USERNAME, UCT_PASSWORD: Portal credentials if login is required
- UCT_FIRST_NAME, UCT_LAST_NAME, UCT_EMAIL, UCT_PHONE, UCT_ID, UCT_PROGRAM
- UCT_DOC_ID, UCT_DOC_TRANSCRIPT: Paths to files for uploads

## Testing and CI
- GitHub Actions: Use Actions tab to run workflows if configured
- Railway: Trigger deployment from Railway dashboard if configured
- Logs: gmail_bot.log and uct_bot.log are generated locally by bots

## Notes
- Gmail signup may use anti-bot checks; this is best-effort automation for dev/test.
- Adapt selectors/flows as university portals evolve.
