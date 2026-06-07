# Oracle Cloud Free Tier — Complete Setup Guide

## What You Get (Always Free)
- 1x ARM VM: up to **4 OCPU + 24 GB RAM**
- 2x AMD VMs: 1 GB RAM each
- 2x Oracle Autonomous Databases
- 200 GB block storage
- 10 TB data transfer/month

## Step 1: Create Oracle Cloud Account

1. Go to **[cloud.oracle.com](https://cloud.oracle.com)**
2. Click **"Start for free"** or **"Sign up"**
3. Enter your details:
   - Name, email, country
   - **Home region**: Choose one close to you (e.g., `us-ashburn-1` for US East, `uk-london-1` for Europe)
4. Add a **credit/debit card** — Oracle verifies it with a $1 temporary hold, then releases it. You will NOT be charged for Always Free resources.
5. Wait for the account to activate (usually instant, sometimes a few hours).

## Step 2: Create Your Free VM

1. Log in to the [Oracle Cloud Console](https://cloud.oracle.com)
2. Click the **hamburger menu (≡)** → **Compute** → **Instances**
3. Click **"Create instance"**
4. Configure:
   - **Name**: `caleb-records-server`
   - **Placement**: Keep defaults
   - **Image**: Change to **Canonical Ubuntu** → **Ubuntu 22.04**
   - **Shape**: Click **"Change shape"** → **VM.Standard.A1.Flex** (ARM-based, Always Free eligible)
   - **OCPUs**: Drag to **4**
   - **Memory**: Drag to **24 GB**
   - **Boot volume**: Change to **50 GB**
   - **Add SSH keys**: Select **"Generate SSH key pair for me"** → Download both `.key` and `.pub` files. Save them somewhere safe.
   - **Virtual cloud network**: Keep default
   - **Public subnet**: Keep default
   - **Assign public IP address**: ✅ Checked
5. Click **"Create"**
6. Wait ~2 minutes for the instance to be **RUNNING**
7. Note the **Public IP address** (e.g., `152.67.123.45`)

## Step 3: Open Firewall Ports

1. In your instance details, click the **Subnet** link
2. Click the **Default security list**
3. Click **"Add Ingress Rules"**
4. Add these rules one by one:

| State | Source CIDR | IP Protocol | Destination Port Range |
|-------|-------------|-------------|------------------------|
| Stateless | `0.0.0.0/0` | TCP | `22` (SSH) |
| Stateless | `0.0.0.0/0` | TCP | `80` (HTTP) |
| Stateless | `0.0.0.0/0` | TCP | `443` (HTTPS) |
| Stateless | `0.0.0.0/0` | TCP | `8000` (API — optional for testing) |

5. Click **"Add Ingress Rules"**

## Step 4: Connect to Your Server

On your Linux machine, open a terminal:

```bash
# Make the private key readable
chmod 600 ~/Downloads/ssh-key-*.key

# SSH into the server (replace with YOUR public IP)
ssh -i ~/Downloads/ssh-key-*.key ubuntu@152.67.123.45
```

> Replace `152.67.123.45` with your actual Public IP.

## Step 5: Install Docker & Docker Compose

Once connected to the server, run:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu
newgrp docker

# Install Docker Compose plugin
sudo apt install docker-compose-plugin -y

# Verify
docker --version
docker compose version
```

## Step 6: Clone & Configure

```bash
# Clone your repo
git clone https://github.com/YOUR_USERNAME/caleb-records.git
cd caleb-records

# Create production env file
cp .env.example .env
nano .env
```

Edit `.env` with these values:

```env
DB_USER=calebrecords
DB_PASSWORD=STRONG_PASSWORD_HERE_CHANGE_THIS
DB_NAME=calebrecords
DATABASE_URL=postgresql://calebrecords:STRONG_PASSWORD_HERE_CHANGE_THIS@db:5432/calebrecords
SECRET_KEY=COPY_OUTPUT_FROM_BELOW_COMMAND
CORS_ORIGINS=http://localhost:5173,http://localhost:5174,https://tauri.localhost
MAX_FILE_SIZE=10485760
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
SMTP_FROM=noreply@calebuniversity.edu.ng
```

Generate a secret key:
```bash
openssl rand -hex 32
```
Copy the output into `SECRET_KEY=` in `.env`.

Save and exit nano: `Ctrl+O`, `Enter`, `Ctrl+X`

## Step 7: Launch Everything

```bash
docker compose up -d --build
```

This downloads PostgreSQL, builds your backend, and starts Nginx. Takes ~3-5 minutes first time.

## Step 8: Create Database Tables

```bash
docker compose exec backend python -c "
from main import Base, engine
Base.metadata.create_all(bind=engine)
print('Tables created')
"
```

## Step 9: Seed Reference Data

```bash
docker compose exec backend python -c "
from main import seed_data, SessionLocal
db = SessionLocal()
seed_data(db)
print('Reference data seeded')
"
```

## Step 10: Test the API

```bash
curl http://YOUR_SERVER_IP/health
```

You should see: `{"status":"ok","timestamp":"..."}`

## Step 11: Set Up a Domain (Optional but Recommended)

If you have a domain (e.g., `records.calebuniversity.edu.ng`):

1. Point an **A record** to your server's Public IP
2. Wait for DNS propagation (~5-30 min)
3. Install SSL:

```bash
sudo apt install certbot -y
sudo certbot certonly --standalone -d records.calebuniversity.edu.ng
sudo cp /etc/letsencrypt/live/records.calebuniversity.edu.ng/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/records.calebuniversity.edu.ng/privkey.pem nginx/ssl/
```

4. Edit `nginx/nginx.conf` — uncomment the HTTPS server block
5. Restart: `docker compose restart nginx`

## Step 12: Update Your Apps

### Mobile App (Student)
1. Open the app → ⚙️ Settings
2. Enter: `http://YOUR_SERVER_IP` (or `https://your-domain.com`)
3. Save → restart app

### Desktop App
The desktop launcher opens the web portals. Users just need the backend running.

### Staff Portal (Web)
Staff can open `http://YOUR_SERVER_IP` in any browser, or you can deploy the staff frontend separately to Vercel/Netlify for free.

## Maintenance Commands

```bash
# View logs
docker compose logs -f backend
docker compose logs -f db

# Restart everything
docker compose restart

# Backup database
docker compose exec db pg_dump -U calebrecords calebrecords > backup_$(date +%F).sql

# Update after code changes
git pull
docker compose up -d --build
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Can't SSH | Check security list has port 22 open |
| Can't reach API | Check security list has port 80 open |
| `docker: permission denied` | Run `newgrp docker` or log out and back in |
| Database connection failed | Check `.env` `DATABASE_URL` matches `DB_PASSWORD` |
| Out of memory | The ARM VM has 24 GB — shouldn't happen. If it does, add swap: `sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile` |
