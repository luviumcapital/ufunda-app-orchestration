# Setup Instructions

## Overview
This guide helps you set up and run Ufunda App Orchestration with the new Gmail and UCT bots.

## Prerequisites
- Python 3.10 or higher
- Chrome/Chromium browser
- Internet access to download WebDriver via webdriver-manager

## Installation
### 1. Clone the Repository
```bash
git clone https://github.com/luviumcapital/ufunda-app-orchestration.git
cd ufunda-app-orchestration
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install University Bots Dependencies
```bash
pip install -r university_bots/requirements.txt
```

## Running Local Tests
### Gmail Bot
```bash
python university_bots/gmail_bot.py
```
- Generates gmail_bot.log and credentials text file on success
- Note: Google may show anti-bot/CAPTCHA flows that block automation

### UCT Bot (Sample)
```bash
python university_bots/uct_bot.py
```
- Navigates to UCT portal (default: https://www.uct.ac.za/apply)
- Logs written to uct_bot.log

## Environment Variables (optional)
Create a .env file or export variables in your shell:
```bash
export UCT_PORTAL_URL="https://applyonline.uct.ac.za"  # example
export UCT_USERNAME="username"
export UCT_PASSWORD="password"
export UCT_FIRST_NAME="Test"
export UCT_LAST_NAME="Applicant"
export UCT_EMAIL="test.applicant@example.com"
export UCT_PHONE=""
export UCT_ID=""
export UCT_PROGRAM="Computer Science"
export UCT_DOC_ID="/path/to/id.pdf"
export UCT_DOC_TRANSCRIPT="/path/to/transcript.pdf"
```

## CI and Deployment
- GitHub Actions: Open the Actions tab and run available workflows if configured
- Railway: Trigger a redeploy from the Railway dashboard if the project is connected

## Troubleshooting
- Update Chrome to latest and rerun if WebDriver errors occur
- For Gmail, human verification/CAPTCHA will prevent full automation; test flows manually when prompted
- Check logs: gmail_bot.log and uct_bot.log for errors
