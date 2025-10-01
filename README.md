# Telegram Onboarding Bot

This repository contains a Telegram onboarding bot that collects new-employee information and stores it into Google Sheets.

## Quick start

1. Copy `.env.example` to `.env` and fill your real secrets. Do **not** commit `.env`.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run locally:

```bash
python bot.py
```

## Deploy

Push to GitHub and connect the repository to a cloud runner (Railway, Replit, Render). Make sure to set the environment variables in the runner's dashboard.

## Environment variables

- `BOT_TOKEN` — Telegram bot token
- `HR_TELEGRAM_USERNAME` — e.g. @AnjaliCAHR
- `SPREADSHEET_ID` — Google Sheets ID
- `GOOGLE_CREDS_JSON_CONTENT` — entire JSON content of the service account key
- `ONBOARDING_IMAGE_URL` — Google Drive direct-download URL for the image

## Security

Rotate credentials if exposed and use platform secrets (GitHub Secrets, runner env vars) for deployment.
