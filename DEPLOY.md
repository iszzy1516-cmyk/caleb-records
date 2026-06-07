# Production Deployment Guide

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Nginx     │────▶│  FastAPI    │────▶│  PostgreSQL │
│  (proxy)    │     │  (backend)  │     │   (database)│
└─────────────┘     └─────────────┘     └─────────────┘
```

## Quick Start (Docker)

### 1. Provision a VPS

Recommended: **Ubuntu 22.04 LTS** with at least:
- 2 vCPU
- 4 GB RAM
- 40 GB SSD

Providers: DigitalOcean ($24/mo), AWS Lightsail ($10/mo), Linode, Hetzner

### 2. Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

### 3. Clone & Configure

```bash
git clone https://github.com/YOUR_USERNAME/caleb-records.git
cd caleb-records
cp .env.example .env
nano .env
```

Edit `.env`:
- `DB_PASSWORD` → strong random password
- `SECRET_KEY` → `openssl rand -hex 32`
- `CORS_ORIGINS` → your production domains
- `SMTP_*` → your email server credentials

### 4. Launch

```bash
docker compose up -d --build
```

This starts:
- PostgreSQL on port 5432 (internal)
- FastAPI on port 8000 (internal)
- Nginx on port 80 (public)

### 5. Create Database Tables

```bash
docker compose exec backend python -c "
from main import Base, engine
Base.metadata.create_all(bind=engine)
print('Tables created')
"
```

### 6. Seed Reference Data

```bash
docker compose exec backend python -c "
from main import seed_data, SessionLocal
db = SessionLocal()
seed_data(db)
print('Reference data seeded')
"
```

### 7. Set Up SSL (Let's Encrypt)

```bash
sudo apt install certbot
sudo certbot certonly --standalone -d records.calebuniversity.edu.ng
sudo cp /etc/letsencrypt/live/records.calebuniversity.edu.ng/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/records.calebuniversity.edu.ng/privkey.pem nginx/ssl/
```

Uncomment the HTTPS server block in `nginx/nginx.conf`, then:

```bash
docker compose restart nginx
```

### 8. Update Mobile & Desktop Apps

In the **Settings** page of the student app, enter:
```
https://records.calebuniversity.edu.ng
```

For the desktop app launcher, you can set the default URL in the code or document it.

## Migrating from SQLite to PostgreSQL

If you have existing data in `caleb_records.db`:

```bash
# 1. Dump SQLite to SQL
sqlite3 backend/caleb_records.db .dump > dump.sql

# 2. Convert syntax for PostgreSQL
sed -i 's/INTEGER PRIMARY KEY AUTOINCREMENT/SERIAL PRIMARY KEY/g' dump.sql
sed -i "s/'t'/true/g; s/'f'/false/g" dump.sql

# 3. Import into PostgreSQL
docker compose cp dump.sql db:/tmp/dump.sql
docker compose exec db psql -U calebrecords -d calebrecords -f /tmp/dump.sql
```

> Note: Complex migrations may need manual adjustment. Test on a backup first.

## Maintenance

```bash
# View logs
docker compose logs -f backend
docker compose logs -f db

# Backup database
docker compose exec db pg_dump -U calebrecords calebrecords > backup_$(date +%F).sql

# Update deployment
git pull
docker compose up -d --build

# Restart services
docker compose restart
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Connection refused` | Check `DATABASE_URL` points to `db:5432` |
| CORS errors | Add your domain to `CORS_ORIGINS` in `.env` |
| Uploads fail | Ensure `uploads_data` Docker volume exists |
| Email not sending | Verify SMTP credentials and `SMTP_FROM` |
| Slow queries | Add PostgreSQL indexes; check `pool_size` |

## Production Checklist

- [ ] Strong `SECRET_KEY` set
- [ ] PostgreSQL password changed from default
- [ ] SSL/HTTPS enabled
- [ ] Firewall rules: only 80/443 open
- [ ] Automatic backups configured
- [ ] SMTP credentials working
- [ ] CORS origins restricted to production domains
- [ ] File storage moved to S3 (optional but recommended)
- [ ] Monitoring set up (optional: UptimeRobot, Datadog)
