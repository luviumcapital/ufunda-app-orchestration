# Setup Instructions

## Overview
This guide will help you set up and run the Ufunda Application Orchestration system.

## Prerequisites

- Python 3.9 or higher
- Gmail API credentials
- Chrome/Chromium browser (for Selenium)
- PostgreSQL or SQLite (for database)
- Redis (optional, for production scaling)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/luviumcapital/ufunda-app-orchestration.git
cd ufunda-app-orchestration
```

### 2. Set Up Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Orchestrator Dependencies

```bash
cd orchestrator
pip install -r requirements.txt
```

### 4. Install Gmail Bot Dependencies

```bash
cd ../gmail_bot
pip install -r requirements.txt
```

### 5. Install University Bot Dependencies

```bash
cd ../university_bots
pip install -r requirements.txt
```

## Configuration

### Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download credentials and save as `gmail_bot/credentials.json`

### Environment Variables

Create a `.env` file in the root directory:

```env
# Orchestrator Configuration
ORCHESTRATOR_HOST=0.0.0.0
ORCHESTRATOR_PORT=8000

# Gmail Bot Configuration
GMAIL_CREDENTIALS_PATH=gmail_bot/credentials.json
GMAIL_TOKEN_PATH=gmail_bot/token.json

# Database Configuration
DATABASE_URL=sqlite:///./ufunda.db
# For PostgreSQL: postgresql://user:password@localhost/ufunda

# Bot Configuration
UNIVERSITY_BOT_BASE_URL=http://localhost:8001

# Application Data
APPLICANT_FIRST_NAME=
APPLICANT_LAST_NAME=
APPLICANT_EMAIL=
APPLICANT_PHONE=
```

## Running the System

### Start the Orchestrator

```bash
cd orchestrator
python master_orchestrator.py
```

The orchestrator will start on `http://localhost:8000`

### Start the Gmail Bot

```bash
cd gmail_bot
python gmail_monitor.py
```

The Gmail bot will:
1. Monitor your inbox for university emails
2. Parse application links
3. Send notifications to the orchestrator

### Start University Bots

Each university bot runs as a separate service:

```bash
cd university_bots/bots
python example_university_bot.py
```

## Testing the API

### Check Orchestrator Status

```bash
curl http://localhost:8000/
```

### Submit Test Email Notification

```bash
curl -X POST http://localhost:8000/email/notify \
  -H "Content-Type: application/json" \
  -d '{
    "email_id": "test123",
    "university_name": "Test University",
    "application_link": "https://example.com/apply",
    "subject": "Application Invitation",
    "received_at": "2025-10-28T13:00:00"
  }'
```

### Check Application Status

```bash
curl http://localhost:8000/applications/list
```

## Architecture Components

### 1. Master Orchestrator (Port 8000)
- Central coordination server
- Receives email notifications
- Triggers appropriate bots
- Tracks application status

### 2. Gmail Bot
- Monitors Gmail inbox
- Identifies university emails
- Extracts application links
- Sends to orchestrator

### 3. University Bots
- Portal-specific automation
- Fill application forms
- Submit applications
- Report status back

## Adding a New University Bot

1. Copy the bot template:
```bash
cp university_bots/bot_template.py university_bots/bots/new_university_bot.py
```

2. Customize the bot:
- Update university-specific selectors
- Implement form filling logic
- Add validation steps

3. Register the bot in the orchestrator:
- Update bot routing logic
- Add university name mapping

## Troubleshooting

### Gmail Authentication Issues
- Delete `gmail_bot/token.json` and re-authenticate
- Check OAuth consent screen settings
- Verify API is enabled

### Bot Failures
- Check browser driver version
- Verify element selectors are up to date
- Review application logs

### Database Issues
- Ensure database is accessible
- Check connection string
- Verify migrations are applied

## Development

### Running in Development Mode

```bash
# Orchestrator with auto-reload
uvicorn orchestrator.master_orchestrator:app --reload
```

### Viewing Logs

Logs are written to console by default. Configure file logging in production.

## Production Deployment

### Recommended Setup

1. Use PostgreSQL for database
2. Deploy orchestrator with Gunicorn/Uvicorn workers
3. Use Redis for task queue
4. Set up monitoring and alerting
5. Use environment-specific configuration

### Docker Deployment (Coming Soon)

```bash
docker-compose up
```

## Support

For issues and questions, please open an issue on GitHub.

## License

This project is proprietary to Luvium Capital.
