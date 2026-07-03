# CU-Records AWS Development Environment

Infrastructure as Code (IaC) for deploying CU-Records on AWS Free Tier using **Terraform** and **Ansible**.

## Architecture

```
┌─────────────┐     ┌─────────────────────────────────────┐
│   Internet  │────▶│  EC2 t3.micro (Ubuntu 22.04)        │
└─────────────┘     │  ┌─────────┐ ┌─────────┐ ┌────────┐ │
                    │  │  Nginx  │ │ FastAPI │ │PostgreSQL│ │
                    │  │ (proxy) │ │(backend)│ │ (Docker) │ │
                    │  └─────────┘ └─────────┘ └────────┘ │
                    │  ┌─────────┐ ┌───────────────┐       │
                    │  │ Student │ │ Staff         │       │
                    │  │ Frontend│ │ Frontend      │       │
                    │  └─────────┘ └───────────────┘       │
                    └─────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ S3 Backup Bucket│
                    └─────────────────┘
```

All services run in Docker containers on a single EC2 instance. This keeps costs within AWS Free Tier limits.

## Prerequisites

- AWS Free Tier account
- AWS CLI installed and configured (`aws configure`)
- Terraform >= 1.0
- Ansible >= 2.12
- SSH key pair (existing or generated)

## Generate SSH Key (if needed)

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/culrecords-deployer -C "culrecords-deployer"
```

This creates:
- `~/.ssh/culrecords-deployer` (private key)
- `~/.ssh/culrecords-deployer.pub` (public key)

## Step 1: Configure Terraform

```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
aws_region       = "us-east-1"
key_name         = "culrecords-deployer"
public_key_path  = "~/.ssh/culrecords-deployer.pub"
allowed_ssh_cidr = "YOUR_IP/32"  # e.g. "203.0.113.10/32"
db_password      = "your-strong-db-password"
secret_key       = "your-64-char-hex-secret"
```

Generate a secret key:
```bash
openssl rand -hex 32
```

## Step 2: Deploy Infrastructure

Terraform will automatically generate the Ansible inventory and a group_vars example file.

```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

After deployment, Terraform creates:
- `../ansible/inventory.ini` — points to your new EC2 instance
- `../ansible/group_vars/all.yml.example` — pre-filled with your Terraform values

You can also view outputs manually:
```bash
terraform output server_public_ip
terraform output ssh_command
terraform output s3_backup_bucket
```

## Step 3: Configure Ansible

```bash
cd ../ansible
cp group_vars/all.yml.example group_vars/all.yml
```

Review and edit `group_vars/all.yml`. At minimum, update:
- `db_password` — copy from `terraform.tfvars`
- `secret_key` — copy from `terraform.tfvars`
- `git_repo` — your GitHub repository URL
- `domain_name` — optional, only if you have a domain
- `smtp_*` — optional, only if you want email sending

The `s3_backup_bucket` and `cors_origins` are already pre-filled from Terraform.

## Step 4: Deploy Application

```bash
ansible-playbook -i inventory.ini playbook.yml
```

## Step 5: Verify Deployment

```bash
curl http://YOUR_SERVER_IP/health
```

You should see:
```json
{"status":"ok","timestamp":"..."}
```

## Access Points

| Service | URL |
|---------|-----|
| Student portal | `http://YOUR_SERVER_IP/` |
| Staff portal | `http://YOUR_SERVER_IP/staff/` |
| API health | `http://YOUR_SERVER_IP/health` |

## Optional: Use a Domain + SSL

1. Point an A record to your Elastic IP
2. Set `domain_name` in Terraform and Ansible
3. Set `use_ssl: true` in Ansible
4. Re-run Ansible: `ansible-playbook -i inventory.ini playbook.yml`

> Note: Certbot standalone mode requires port 80. Since Docker Nginx uses port 80, you may need to temporarily stop the container (`docker compose stop nginx`), run certbot, then update `nginx/nginx.conf` with the SSL block and restart.

## Costs

All resources are AWS Free Tier eligible for 12 months:
- EC2 t3.micro: 750 hours/month
- EBS 20GB gp3 storage
- S3 5GB standard storage
- Data transfer: within limits

## Destroy Infrastructure

```bash
cd infrastructure/terraform
terraform destroy
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Permission denied (publickey)` | Ensure private key permissions are `chmod 600` |
| `Connection refused` on /health | Wait 2-3 minutes for Docker build, check `docker compose logs` |
| CORS errors | Update `cors_origins` in Ansible group_vars |
| SSL fails | Ensure domain DNS points to the Elastic IP before running Certbot |
