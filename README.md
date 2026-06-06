# Caleb University Records Management System

A complete records management system for Caleb University, featuring a FastAPI backend, dual React portals (Student & Staff), and a Tauri desktop launcher.

## Architecture

```
.
├── backend/           # FastAPI + SQLAlchemy + SQLite
├── frontend/          # Student Portal (React + Vite, port 5173)
├── frontend-staff/    # Staff Portal (React + Vite, port 5174)
└── desktop/           # Tauri Desktop Launcher
```

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Student Portal

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

### 3. Staff Portal

```bash
cd frontend-staff
npm install
npm run dev        # http://localhost:5174
```

### 4. Desktop App

```bash
cd desktop
npm install
npm run tauri dev  # Native desktop window
```

## Key Features

- **Dual Portal System** — completely separate Student and Staff UIs sharing one database
- **JWT Authentication** — role-based access control (staff vs student)
- **Document Management** — upload, download, deadline enforcement, late fees
- **Auto-Alerts** — students see alerts for missing required documents
- **Real-Time Stats** — live dashboard counts (no fake data)
- **Self-Registration** — students can register with cascading college→dept→program
- **Password Reset** — token-based reset via email (SMTP or console fallback)
- **Audit Logging** — all actions logged with user and timestamp
- **Rate Limiting** — slowapi protection on public endpoints
- **Database Optimization** — indexes, connection pooling, eager loading, pagination
- **Desktop Launcher** — Tauri app for native window management

## Default Credentials

| Portal | Username | Password |
|--------|----------|----------|
| Staff  | `admin`  | `admin123` |
| Student | (self-register at `/register`) | `Caleb{yy}` (e.g., `Caleb24`) |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key | (hardcoded fallback) |
| `CORS_ORIGINS` | Allowed CORS origins | `localhost:5173,5174,8000` |
| `SMTP_HOST` | Email server host | (none) |
| `MAX_FILE_SIZE` | Max upload size (bytes) | 10MB |
| `CUL_BACKEND_PATH` | Backend path for desktop app | auto-detected |

## Production Checklist

- [ ] PostgreSQL instead of SQLite
- [ ] httpOnly cookies instead of localStorage
- [ ] S3/Cloudinary for file storage
- [ ] Proper SMTP credentials
- [ ] Rotate `SECRET_KEY`
- [ ] HTTPS only
- [ ] Signed desktop app bundles (code signing)

## License

© 2024 Caleb University. All rights reserved.
# caleb-records
