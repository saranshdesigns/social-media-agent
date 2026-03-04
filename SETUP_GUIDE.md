# Social Media Automation Agent — Setup Guide

## Step 1: Install Backend Dependencies

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
```

## Step 2: Configure .env

```bash
cp .env.example .env
# Fill in all values in .env
```

Required values:
- `OPENAI_API_KEY` — from platform.openai.com
- `GOOGLE_CREDENTIALS_PATH` — path to your existing credentials.json
- `GOOGLE_PORTFOLIO_FOLDER_ID` — from the Drive folder URL
- `SERVER_BASE_URL` — http://localhost:8000 (local) or Railway URL (production)
- `FACEBOOK_PAGE_ACCESS_TOKEN` + `FACEBOOK_PAGE_ID` — from Meta Developer App
- `INSTAGRAM_ACCOUNT_ID` — Instagram Business Account ID
- `LINKEDIN_ACCESS_TOKEN` + `LINKEDIN_PERSON_URN` — from LinkedIn Developer App
- `PINTEREST_ACCESS_TOKEN` + `PINTEREST_BOARD_ID` — from Pinterest Developer App
- `SECRET_KEY` — any random string (generate: `python -c "import secrets; print(secrets.token_hex(32))"`)

> No Cloudinary needed. Images are temporarily served by the FastAPI server itself at /temp/

## Step 3: Initialize Database

```bash
python database.py
```

## Step 4: Test Run (Optional)

```bash
python scheduler.py   # runs one posting cycle immediately
```

## Step 5: Start Backend

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Step 6: Install & Run Frontend

```bash
cd ../frontend
npm install
cp .env.local.example .env.local
# Set NEXT_PUBLIC_API_URL if your backend is not on localhost:8000

npm run dev   # development
npm run build && npm start   # production
```

---

## Deployment on Railway.app

### Backend
1. Create new project → Deploy from GitHub
2. Select the `backend/` folder as root
3. Add all `.env` variables in Railway dashboard → Variables
4. Set `SERVER_BASE_URL` to your Railway backend URL (e.g. `https://your-app.up.railway.app`)
5. Railway auto-detects `Procfile` and starts the server

### Frontend
1. Create another Railway service → select `frontend/` folder
2. Set `NEXT_PUBLIC_API_URL` to your backend Railway URL
3. Railway auto-detects Next.js and builds it

---

## Google Drive Credentials

Since you already have a Google Cloud project with Drive API enabled:

**Option A — Service Account (Recommended for server deployment)**
1. Go to Google Cloud Console → IAM & Admin → Service Accounts
2. Create new service account → Download JSON key
3. Share your Portfolio folder with the service account email (view only)
4. Set `GOOGLE_CREDENTIALS_PATH=path/to/service-account.json`

**Option B — OAuth2 (Same as your chatbot)**
1. Use your existing `credentials.json` from Google Cloud Console
2. First run will open browser for authorization → creates `token.json`
3. Copy `token.json` to server after first auth

---

## Platform API Setup Links

| Platform | Developer Console |
|---|---|
| Facebook + Instagram | developers.facebook.com |
| LinkedIn | developer.linkedin.com |
| Pinterest | developers.pinterest.com |

---

## File Structure

```
Social Media Assistant/
├── .env.example              ← Copy to .env and fill in
├── .gitignore
├── SETUP_GUIDE.md
├── backend/
│   ├── main.py               ← FastAPI entry point
│   ├── config.py             ← All settings via .env
│   ├── database.py           ← SQLite setup + helpers
│   ├── scheduler.py          ← Daily job orchestrator
│   ├── requirements.txt
│   ├── Procfile              ← Railway deployment
│   ├── runtime.txt
│   ├── temp/                 ← Temp image files (auto-created, served at /temp/)
│   ├── modules/
│   │   ├── drive_watcher.py  ← Google Drive scanner (read-only)
│   │   ├── image_processor.py← Pillow resize + local temp serve
│   │   ├── caption_engine.py ← OpenAI GPT-4o-mini captions
│   │   ├── retry_handler.py  ← Auto-retry logic
│   │   └── poster/
│   │       ├── instagram.py
│   │       ├── facebook.py
│   │       ├── linkedin.py
│   │       └── pinterest.py
│   └── api/
│       └── routes/
│           └── dashboard.py  ← REST API endpoints
├── frontend/                 ← Next.js dashboard
│   └── src/
│       ├── app/
│       │   ├── page.tsx      ← Overview
│       │   ├── history/      ← Posted images
│       │   ├── logs/         ← Error/success logs
│       │   ├── platforms/    ← API connection status
│       │   └── settings/     ← Config view
│       ├── components/
│       │   └── Sidebar.tsx
│       └── lib/
│           └── api.ts        ← Backend API client
└── data/
    └── database.db           ← Auto-created on first run
```
