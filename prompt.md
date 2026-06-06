# Caleb University Student Records Management System
## AI Development Prompt / Handoff Document

**Version:** 1.0  
**Date:** 2026-06-06  
**Author:** Israel Johnson  
**Context:** Built for Caleb University, Lagos (CUL) to replace paper-based student record folders.  
**Time Constraint:** 2-day build. FastAPI backend + React frontend + Tauri desktop + Capacitor mobile.

---

## 1. Project Goal

Replace the university's paper folder system with a digital records platform that:
- Stores student admission documents permanently (Clearance Cert, JAMB Result, WAEC/NECO Result, JAMB Admission Letter, Birth Certificate, etc.)
- Tracks **Clearance Certificates per level** (100, 200, 300, 400, 500) — a new one is required each time a student advances
- Prevents "missing files" by enforcing document completeness reports
- Provides role-based access for staff (Records Officer, Lecturer, Bursar, HOD, Admin)
- Offers a public student portal (mobile-friendly) where students view their own records by matric number
- Generates audit logs for every action (who uploaded what, when)
- Auto-calculates CGPA from academic records

---

## 2. Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| **Backend** | FastAPI + SQLAlchemy + SQLite | Zero-config DB, auto-generated OpenAPI docs, async-capable, Python-native |
| **Auth** | JWT (python-jose) + bcrypt (passlib) | Stateless tokens, industry-standard hashing |
| **File Storage** | Local disk (`uploads/` folder) + Multer-like handling via `python-multipart` | Simple for 2-day build; migrate to S3/Cloudinary for production |
| **Frontend** | React 18 + Vite + React Router | Single codebase shared across web, desktop, mobile |
| **Desktop** | Tauri (Rust wrapper) | Native desktop app from same React code |
| **Mobile** | Capacitor (Android wrapper) | Native APK from same React code |
| **Deployment** | Uvicorn (dev) / Render or Railway (prod) | Lightweight, single-process |

---

## 3. System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React UI      │────▶│  FastAPI API    │────▶│   SQLite DB     │
│  (Web/Desktop/  │◄────│  (Port 8000)    │◄────│  (Single File)  │
│   Mobile)       │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │ uploads/     │
                        │ (Documents)  │
                        └──────────────┘
```

**Key Design Decisions:**
- One React frontend, three deployment targets (web, Tauri desktop, Capacitor mobile)
- SQLite for zero-setup deployment; can migrate to PostgreSQL later by changing the connection string
- JWT tokens stored in `localStorage` (acceptable for internal school network; switch to httpOnly cookies for production)
- Public student lookup endpoint (`/api/public/students/{matric}`) requires NO auth — students use this on their phones

---

## 4. Database Schema (SQLAlchemy Models)

### 4.1 Tables

| Table | Purpose |
|-------|---------|
| `colleges` | Caleb's 8 colleges (COLED, COLENSMA, COPAS, CASMAS, CONBAMS, COBMAHS, COCMS, COLAW) |
| `departments` | Departments within each college |
| `programs` | Degree programs (B.Sc. Computer Science, LL.B., etc.) |
| `students` | Core student profile with auto-generated matric numbers |
| `documents` | Uploaded files (PDFs, images) with `document_type` and `level` (for clearance certs) |
| `courses` | Course catalog (code, title, credit units, level, semester) |
| `academic_records` | Grades per student per course |
| `users` | Staff accounts with roles |
| `audit_logs` | Immutable log of every create/update/upload action |

### 4.2 Critical Schema Details

**Matric Number Format:** `CUL/{admission_year}/{sequence:04d}`  
Example: `CUL/2024/0001`

**Document Model — `level` Column:**
- `NULL` for one-time documents (JAMB result, WAEC, birth cert, admission letter)
- `100`, `200`, `300`, `400`, `500` for **Clearance Certificates** (required per level)

**Document Types (Enum):**
- `clearance_cert` — **Level-specific image/PDF**
- `jamb_result`
- `waec_result`
- `jamb_admission_letter`
- `birth_certificate`
- `passport_photo`
- `medical`
- `fee_receipt`
- `transcript`

---

## 5. API Endpoints

### 5.1 Authentication
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/token` | None | OAuth2Password form login, returns JWT + role |

### 5.2 Reference Data (Protected)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/colleges` | JWT | List all 8 colleges |
| GET | `/api/departments?college_id=` | JWT | Filtered departments |
| GET | `/api/programs?department_id=` | JWT | Filtered programs |
| GET | `/api/courses?level=&dept_id=` | JWT | Course catalog |

### 5.3 Student Management (Protected)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/students` | JWT | Register student, auto-generates matric |
| GET | `/api/students/search?q=` | JWT | Fuzzy search by matric/name |
| GET | `/api/students/{id}` | JWT | Full profile + docs + grades + CGPA |

### 5.4 Documents (Protected Upload, Public Download)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/documents` | JWT | Upload file with `student_id`, `document_type`, `level` (for clearance), `file` |
| GET | `/api/documents/{id}/download` | **None** | Download original file with `Content-Disposition: attachment` |

> **Security Note:** Download is public because doc IDs are not sequential/guessable in practice, and this is an internal school network. For production, add a short-lived signed URL or require auth.

### 5.5 Grades (Protected)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/grades` | JWT (Lecturer/Admin/HOD) | Record grade for a student in a course |
| GET | `/api/students/{id}/cgpa` | JWT | Auto-calculated CGPA (5-point scale: A=5, B=4, C=3, D=2, E=1, F=0) |

### 5.6 Reports & Audit (Admin/Records/HOD)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/reports/missing-documents` | JWT | Lists all students missing required docs, including missing clearance for their **current level** |
| GET | `/api/audit-logs?limit=50` | JWT (Admin only) | Immutable action log |

### 5.7 Public Student Portal (No Auth)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/public/students/{matric_number}` | None | Student self-service lookup by matric |

---

## 6. Security Architecture & Optimizations

### 6.1 Authentication & Authorization
- **Password hashing:** `bcrypt` via `passlib` with default rounds
- **JWT:** HS256 signed with `SECRET_KEY`. Token expiry: 8 hours (`ACCESS_TOKEN_EXPIRE_MINUTES = 480`)
- **Role-based access control (RBAC):**
  - `admin` — Full access, user management, audit logs
  - `records_officer` — Student CRUD, document upload, missing reports
  - `lecturer` — Grade entry (own courses only in future iterations), view students
  - `bursar` — View fee receipts, flag financial holds
  - `hod` — Department-level reports and oversight
- **Inactive users:** `is_active` flag; disabled users cannot authenticate

### 6.2 Input Validation & Injection Prevention
- **SQL Injection:** Fully prevented via SQLAlchemy ORM (parameterized queries). No raw SQL concatenation.
- **NoSQL/JSON Injection:** Not applicable (SQLite).
- **Form validation:** Pydantic schemas (`StudentCreate`, `GradeCreate`) validate types and constraints server-side.
- **File upload validation:**
  - File size limit: 10MB per upload
  - File extension extracted via `os.path.splitext()` — **NOT secure alone**
  - **TODO:** Add MIME type validation and magic number checking (python-magic) to prevent malicious uploads disguised as PDFs
  - **TODO:** Scan uploaded images for embedded scripts; serve with `Content-Disposition: attachment` to prevent inline execution
- **Filename sanitization:** Original filename is stored for display, but the **stored filename** is a UUID-like safe string: `{matric}_{doctype}_{level}_{timestamp}{ext}`

### 6.3 File Storage Security
- **Storage path:** `uploads/` directory outside of web root (not served as static by default)
- **Access control:** Files are served ONLY via the `/api/documents/{id}/download` endpoint, not directly from disk
- **TODO:** Add file type whitelist: `.pdf`, `.jpg`, `.jpeg`, `.png` only
- **TODO:** Add virus scanning (ClamAV integration) for production
- **TODO:** Store files outside the project directory (e.g., `/var/caleb-records/uploads/`) to prevent path traversal if the app is compromised

### 6.4 CORS & Network Security
- **CORS:** Currently `allow_origins=["*"]` — **DANGEROUS for production**
  - **TODO:** Restrict to known origins: `https://records.calebuniversity.edu.ng`, `capacitor://localhost`, `tauri://localhost`
- **TODO:** Add rate limiting (slowapi) to prevent brute force on login and student search
- **TODO:** Add `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security` headers
- **TODO:** Run behind HTTPS only (Traefik / Nginx with Let's Encrypt)

### 6.5 Audit & Accountability
- **Audit log table:** Every `CREATE`, `UPDATE`, `UPLOAD`, `DELETE` is logged with:
  - Username who performed the action
  - Action type
  - Table affected
  - Record ID
  - Human-readable details
  - Timestamp
- **TODO:** Add IP address logging to `audit_logs` table for forensic tracing
- **TODO:** Prevent audit log deletion (separate read-only connection or append-only table)

### 6.6 Data Integrity
- **Foreign keys:** Enabled via `PRAGMA foreign_keys = ON`
- **Unique constraints:** `matric_number`, `username` are UNIQUE
- **TODO:** Add database-level CHECK constraints (e.g., `level` must be 100, 200, 300, 400, 500)
- **TODO:** Add soft deletes for students (mark `status='withdrawn'` instead of DELETE) to preserve audit trail

### 6.7 Secrets Management (CRITICAL TODO)
- **Current:** `SECRET_KEY` is hardcoded in `main.py` as `"caleb-records-secret-CHANGE-IN-PROD"`
- **TODO:** Move `SECRET_KEY` to environment variable: `os.environ.get("SECRET_KEY")`
- **TODO:** Use `.env` file with `python-dotenv` for local dev, never commit `.env` to git
- **TODO:** Rotate `SECRET_KEY` in production and invalidate all existing tokens

### 6.8 Mobile/Desktop Security
- **LocalStorage:** JWT stored in `localStorage` — vulnerable to XSS if frontend is compromised
  - **TODO:** Migrate to httpOnly cookies with `SameSite=Strict` for web
  - **TODO:** For mobile (Capacitor), use Secure Storage plugin instead of localStorage
  - **TODO:** For desktop (Tauri), use Tauri's secure storage API
- **TODO:** Implement token refresh mechanism (short-lived access tokens + long-lived refresh tokens)

---

## 7. Frontend Structure

### 7.1 Pages/Views

| Page | Route | Audience | Key Features |
|------|-------|----------|-------------|
| **Login** | `/` | Staff | OAuth2 form, role-based redirect |
| **Staff Dashboard** | `/staff` | Staff | Search, register, upload docs, enter grades, missing reports, audit logs |
| **Student Portal** | `/student` | Students | Public lookup by matric, view docs, view grades, download files |

### 7.2 Shared Components
- `StudentSearch` — Fuzzy search with result cards
- `DocumentUpload` — Form with dynamic level picker (shows only for clearance_cert)
- `GradeEntry` — Course selection + grade input
- `DocumentChecklist` — Visual ✅/❌ grid for required documents per level
- `MissingDocsReport` — Table of students with incomplete files

### 7.3 Responsive Design
- Mobile-first CSS with `@media (max-width: 768px)` breakpoints
- Grid layouts collapse to single column on mobile
- Tables scroll horizontally on small screens
- Touch-friendly button sizes (min 44px height)

---

## 8. Caleb University Context

### 8.1 Organizational Structure
- **8 Colleges:** COLED, COLENSMA, COPAS, CASMAS, CONBAMS, COBMAHS, COCMS, COLAW
- **Departments:** Computer Science, Cyber Security, Software Engineering, Accounting, Business Admin, Economics, Mass Communication, Law, Early Childhood Education, Architecture, Nursing, etc.
- **Programs:** B.Sc. (4 years), LL.B. (5 years), B.NSc. (Nursing)
- **Motto:** "For God and Humanity"

### 8.2 Admission Requirements (Documents to Track)
1. **Clearance Certificate** — Per level (100, 200, 300, 400, 500). Image or PDF. Required for registration each session.
2. **JAMB Result** — One-time, required for admission
3. **WAEC / NECO Result** — One-time, required for admission
4. **JAMB Admission Letter** — One-time, proof of admission
5. **Birth Certificate** — One-time, demographic verification
6. **Passport Photo** — One-time, ID card generation
7. **Medical Report** — One-time, health screening
8. **Fee Receipt** — Per semester, financial clearance
9. **Transcript** — Generated internally from academic records

### 8.3 Academic Calendar Assumptions
- **Semesters:** First, Second, Third (Summer)
- **Academic Session Format:** `YYYY/YYYY` (e.g., `2024/2025`)
- **Grading:** 5-point scale (A=5, B=4, C=3, D=2, E=1, F=0)
- **Levels:** 100, 200, 300, 400, 500 (depending on program duration)

---

## 9. Known Issues & TODOs

### 9.1 Critical (Fix Before Production)
- [ ] **Hardcoded SECRET_KEY** — Move to environment variable
- [ ] **CORS wildcard** — Restrict to known origins
- [ ] **No HTTPS** — Deploy with SSL/TLS
- [ ] **No rate limiting** — Add `slowapi` to prevent brute force
- [ ] **File type validation** — Whitelist extensions + MIME checking
- [ ] **No file size limit enforcement** — Add middleware check
- [ ] **JWT in localStorage** — XSS risk; move to httpOnly cookies or secure storage
- [ ] **No backup strategy** — Add daily SQLite backup script
- [ ] **No input sanitization on search** — SQL injection theoretically blocked by ORM, but add input length limits

### 9.2 High Priority
- [ ] **Soft deletes** — Prevent accidental student deletion
- [ ] **Document versioning** — Keep old versions when re-uploading
- [ ] **Email notifications** — Notify students when grades are uploaded
- [ ] **Bulk import** — CSV/Excel upload for mass student registration
- [ ] **Transcript PDF generation** — Auto-generate official transcript PDF with watermark
- [ ] **Course allocation** — Link lecturers to specific courses for grade entry restrictions
- [ ] **Fee integration** — Connect to bursary system for automatic fee receipt validation

### 9.3 Medium Priority
- [ ] **Dashboard analytics** — Charts: students per department, missing docs trend, CGPA distribution
- [ ] **Advanced search** — Filter by department, level, admission year, missing doc type
- [ ] **Student self-service upload** — Allow students to upload docs pending staff approval
- [ ] **Multi-campus support** — If Caleb expands to multiple campuses
- [ ] **API rate limiting per user** — Prevent abuse of public endpoints

### 9.4 Low Priority / Nice to Have
- [ ] **Dark mode** — CSS variables for theme switching
- [ ] **Offline mode** — PWA service worker for limited offline access
- [ ] **Biometric auth** — Fingerprint login for staff desktop app
- [ ] **Blockchain verification** — Immutable transcript verification for employers
- [ ] **AI chatbot** — Student FAQ bot for portal queries

---

## 10. Deployment Guide

### 10.1 Development
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
# API docs: http://localhost:8000/docs

# Frontend
cd frontend
npm install
npm run dev
# UI: http://localhost:5173
```

### 10.2 Production (Render/Railway)
```bash
# requirements.txt
fastapi
uvicorn[standard]
sqlalchemy
python-jose[cryptography]
passlib[bcrypt]
python-multipart
python-dotenv  # TODO: add this
slowapi        # TODO: add this
python-magic   # TODO: add this
```

**Environment Variables:**
```env
SECRET_KEY=your-256-bit-secret-here
DATABASE_URL=sqlite:///./caleb_records.db
UPLOAD_DIR=/var/caleb-records/uploads
CORS_ORIGINS=https://records.calebuniversity.edu.ng
MAX_FILE_SIZE=10485760
```

### 10.3 Desktop Build (Tauri)
```bash
cd frontend
npm run build
npx tauri build
# Output: src-tauri/target/release/caleb-records-desktop.exe
```

### 10.4 Mobile Build (Capacitor Android)
```bash
cd frontend
npm run build
npx cap sync
npx cap open android
# In Android Studio: Build → Build Bundle(s) / APK(s) → Build APK
```

---

## 11. Testing Checklist

### 11.1 Backend Tests
- [ ] Register student → verify auto-matric `CUL/2024/0001`
- [ ] Upload clearance cert for 100L → verify `level=100` stored
- [ ] Upload clearance cert for 200L → same student now has 2 clearances
- [ ] Missing docs report → should NOT flag student if all base docs + current level clearance exist
- [ ] Missing docs report → SHOULD flag student if 300L clearance missing when student is at 300L
- [ ] Download document → verify `Content-Disposition: attachment` and correct filename
- [ ] Audit log → verify every upload creates a log entry
- [ ] Role restriction → lecturer cannot access audit logs
- [ ] Invalid login → returns 400, no token
- [ ] Expired token → returns 401

### 11.2 Frontend Tests
- [ ] Staff login → redirect to dashboard
- [ ] Search student by matric → click → profile loads
- [ ] Document checklist → shows ❌ for missing 300L clearance when student is 300L
- [ ] Upload form → selecting "Clearance Certificate" reveals level dropdown
- [ ] Student portal → enter matric → view docs → click download → file saves
- [ ] Mobile view → all tables scrollable, buttons tappable
- [ ] Desktop app → window title correct, no CORS issues (Tauri uses custom protocol)

---

## 12. File Inventory

```
caleb-records/
├── backend/
│   ├── main.py              # Entire FastAPI app (models, routes, auth, seed)
│   ├── requirements.txt     # Dependencies
│   └── uploads/             # Document storage (created at runtime)
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Router + auth state
│   │   ├── index.css        # Global styles + responsive
│   │   └── pages/
│   │       ├── Login.jsx
│   │       ├── StaffDashboard.jsx
│   │       └── StudentPortal.jsx
│   ├── index.html
│   └── package.json
├── desktop/                 # Tauri wrapper (src-tauri/)
├── mobile/                  # Capacitor wrapper (android/)
└── prompt.md                # This file
```

---

## 13. Contact & Context

- **Developer:** Israel Johnson (B.Sc. Computer Science, Caleb University)
- **System Target Users:** Caleb University Records Office, Department HODs, Lecturers, Students
- **Competition Context:** Caleb University 200k Problem-Solving Contest — this system solves the "missing student records" problem
- **YouTube Channel:** Project will be documented as a build series
- **Next AI Session Goal:** Implement the CRITICAL security TODOs (SECRET_KEY env, CORS restriction, file validation, rate limiting) and add the transcript PDF generation feature

---

*End of Document. For God and Humanity.*
