# Ufunda App Orchestration

## Overview
University application workflow automation with orchestrator and bot templates for Gmail and university portals.

This repository contains a modular automation system designed to streamline university applications by orchestrating interactions between email (Gmail) and university application portals.

## Architecture

The system consists of three main components:

1. **Master Orchestrator** - FastAPI-based central controller
2. **Gmail Bot** - Monitors inbox for university emails and extracts application links
3. **University Bots** - Portal-specific automation for completing applications

## Folder Structure

```
ufunda-app-orchestration/
├── orchestrator/
│   ├── master_orchestrator.py    # Main FastAPI orchestration server
│   ├── requirements.txt          # Python dependencies
│   └── config.py                 # Configuration settings
├── gmail_bot/
│   ├── gmail_monitor.py          # Gmail API integration
│   ├── email_parser.py           # Parse university emails
│   └── requirements.txt
├── university_bots/
│   ├── base_bot.py               # Base class for university bots
│   ├── bot_template.py           # Template for new university bots
│   ├── requirements.txt
│   └── bots/
│       └── example_university_bot.py
├── shared/
│   ├── database.py               # Shared database models
│   └── utils.py                  # Common utilities
├── README.md
└── setup_instructions.md
```

## Key Features

- **Centralized Orchestration**: Master orchestrator manages all bot activities
- **Email Monitoring**: Automatic detection of university application emails
- **Portal Automation**: Browser automation for filling application forms
- **Extensible Architecture**: Easy to add new university portal integrations
- **Status Tracking**: Real-time monitoring of application progress

## Workflow

1. Gmail bot monitors inbox for university invitation emails
2. Extracts application links and forwards to orchestrator
3. Orchestrator identifies the university and triggers appropriate bot
4. University bot navigates portal and completes application
5. Status updates sent back to orchestrator
6. Orchestrator logs completion and notifies user

## Technology Stack

- **Orchestrator**: FastAPI, Python
- **Gmail Integration**: Google Gmail API
- **Browser Automation**: Selenium/Playwright
- **Database**: SQLite/PostgreSQL
- **Task Queue**: Redis (optional for scaling)

## Getting Started

Detailed setup instructions are available in `setup_instructions.md`

## Development Status

This is an active development project for the Ufunda university application automation system.
