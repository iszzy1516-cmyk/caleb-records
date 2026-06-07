#!/bin/bash
set -e

echo "=========================================="
echo "Caleb Records — Oracle Cloud VM Setup"
echo "=========================================="

# Step 1: Update system
echo "[1/7] Updating system..."
sudo apt update && sudo apt upgrade -y

# Step 2: Install Docker
echo "[2/7] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "$USER"
    sudo apt install docker-compose-plugin -y
    echo "Docker installed. You may need to log out and back in."
else
    echo "Docker already installed."
fi

# Step 3: Clone repo
echo "[3/7] Cloning repository..."
if [ ! -d "caleb-records" ]; then
    read -p "Enter your GitHub username: " GH_USER
    git clone "https://github.com/${GH_USER}/caleb-records.git"
fi
cd caleb-records

# Step 4: Configure .env
echo "[4/7] Configuring environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    DB_PASS=$(openssl rand -hex 16)
    SECRET=$(openssl rand -hex 32)
    SERVER_IP=$(curl -s ifconfig.me)
    
    sed -i "s|STRONG_PASSWORD_HERE|${DB_PASS}|g" .env
    sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql://calebrecords:${DB_PASS}@db:5432/calebrecords|g" .env
    sed -i "s|SECRET_KEY=|SECRET_KEY=${SECRET}|g" .env
    sed -i "s|CORS_ORIGINS=.*|CORS_ORIGINS=http://localhost:5173,http://localhost:5174,https://tauri.localhost,http://${SERVER_IP},https://${SERVER_IP}|g" .env
    
    echo ""
    echo "✅ .env configured automatically"
    echo "   DB Password: ${DB_PASS}"
    echo "   Secret Key:  ${SECRET}"
    echo "   Server IP:   ${SERVER_IP}"
    echo ""
    echo "Edit .env manually if you need to add SMTP or change anything:"
    echo "   nano .env"
    echo ""
else
    echo ".env already exists, skipping auto-config."
fi

# Step 5: Launch Docker
echo "[5/7] Launching Docker containers..."
docker compose up -d --build

# Step 6: Wait for DB to be ready
echo "[6/7] Waiting for database..."
sleep 15

# Step 7: Create tables and seed data
echo "[7/7] Creating tables and seeding data..."
docker compose exec -T backend python -c "
from main import Base, engine
Base.metadata.create_all(bind=engine)
print('Tables created')
" || true

docker compose exec -T backend python -c "
from main import seed_data, SessionLocal
try:
    db = SessionLocal()
    seed_data(db)
    print('Reference data seeded')
except Exception as e:
    print('Seed may already exist:', e)
" || true

echo ""
echo "=========================================="
echo "🎉 DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "Your server is running at:"
echo "   http://$(curl -s ifconfig.me)"
echo ""
echo "Test the API:"
echo "   curl http://$(curl -s ifconfig.me)/health"
echo ""
echo "View logs:"
echo "   docker compose logs -f backend"
echo ""
echo "Next steps:"
echo "   1. Open student/staff apps"
echo "   2. In Settings, enter: http://$(curl -s ifconfig.me)"
echo "   3. Set up a domain + SSL (see DEPLOY.md)"
echo ""
