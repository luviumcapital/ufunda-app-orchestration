# Setup Instructions
## Overview
This guide helps you set up and run Ufunda App Orchestration with university and bursary bots, including new UJ and NSFAS bots.

## Prerequisites
- Python 3.10 or higher
- Chrome/Chromium browser (or compatible)
- Internet access to download WebDriver via webdriver-manager

## Installation
### 1. Clone the Repository
```
bash
git clone https://github.com/luviumcapital/ufunda-app-orchestration.git
cd ufunda-app-orchestration
```
### 2. Create and Activate Virtual Environment
```
bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```
### 3. Install University Bots Dependencies
```
bash
pip install -r university_bots/requirements.txt
```

## Running Local Tests
### UJ Bot
```
bash
python - <<'PY'
from university_bots.uj_bot import run
print(run(None, {
  'first_name':'Test','last_name':'User','email':'test@example.com',
  'id_number':'0000000000000','mobile':'0710000000',
  'programme':'BSc Computer Science',
  'uploads':{
    'id_doc':'/abs/path/id.pdf','results':'/abs/path/results.pdf',
    'residence_proof':'/abs/path/proof.pdf','affidavit':'/abs/path/affidavit.pdf'
  },
  'fee_waiver': True
}))
PY
```
### NSFAS Bot
```
bash
python - <<'PY'
from university_bots.nsfas_bot import run
print(run(None, {
  'first_name':'Test','last_name':'User','email':'test@example.com',
  'id_number':'0000000000000','mobile':'0710000000',
  'university':'University of Johannesburg', 'programme':'BSc',
  'uploads':{
    'id_doc':'/abs/path/id.pdf','proof_income':'/abs/path/income.pdf',
    'consent_form':'/abs/path/consent.pdf','academic_record':'/abs/path/record.pdf'
  },
  'otp':'123456'
}))
PY
```

## Orchestrator Parallel Run
```
bash
python - <<'PY'
from orchestrator.master_orchestrator import run_parallel_bots
import json
print(json.dumps(run_parallel_bots({'first_name':'Test','last_name':'User','email':'test@example.com'}, bots=['uj','nsfas']), indent=2))
PY
```

## Environment Variables (optional)
- General: BOT_LOG_LEVEL, ARTIFACT_DIR
- UJ context keys: uj_username, uj_password OR email, id_number, mobile; uploads dict; fee_waiver; card_* when paying
- NSFAS context keys: nsfas_email, nsfas_password OR email, id_number, mobile; uploads dict; otp

## Troubleshooting
- Update CSS/ID selectors if portals change their UI.
- Provide a Selenium WebDriver instance to run() if needed for full browser automation.
- Run with verbose logs: export BOT_LOG_LEVEL=DEBUG
