## Goal

Deploy this 3-container Docker Compose app (UI + server + MySQL) to Google Cloud while staying within **free / trial credit** limits.

The simplest + lowest-cost approach is to run Docker Compose on a small **Compute Engine e2-micro** VM.

---

## Option A (recommended for lowest cost): Compute Engine VM + Docker Compose

### 1) Create/Select a GCP project
- In Google Cloud Console, create a **new Project** (recommended) and ensure **Billing** is enabled (your “No-cost trial credit”).

### 2) Enable required APIs
- Enable **Compute Engine API**

### 3) Create a VM (free-tier friendly)
In **Compute Engine → VM instances → Create instance**:

- **Machine type**: `e2-micro`
- **OS**: Ubuntu 22.04 LTS (or Debian)
- **Disk**: keep small (10–20GB is fine)
- **Firewall**:
  - Don’t enable “Allow HTTP/HTTPS traffic” unless you want ports 80/443.
  - We will open only the ports we need (8080/5000) with a custom firewall rule.

> Tip: pick a region that supports the “always free” e2-micro VM if you want to minimize spend.

### 4) Create firewall rules (allow UI + API ports)
Go to **VPC network → Firewall** and create a rule:

- **Targets**: All instances in the network (or use network tags)
- **Source IPv4 ranges**: your IP only (recommended) or `0.0.0.0/0` (not recommended)
- **Protocols/ports**:
  - `tcp:8080` (UI)
  - `tcp:5000` (API)
  - optionally `tcp:8081` (phpMyAdmin) — only if you need it, and ideally restricted to your IP

### 5) SSH into the VM and install Docker + Compose plugin
In the VM details, click **SSH**, then run:

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin git
sudo usermod -aG docker $USER
newgrp docker
docker --version
docker compose version
```

### 6) Clone your GitHub repo
```bash
git clone https://github.com/leenaparik/shivam-demo.git
cd shivam-demo
```

### 7) Create a `.env` on the VM (recommended)
This repo includes `env.example`. Create a real `.env` **on the VM**:

```bash
cp env.example .env
```

Edit `.env` and set:
- `FLASK_SECRET_KEY` (random string)
- `SSN_KEY` (generate this on the VM):

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Paste that into `.env` as `SSN_KEY=...`

### 8) Start the app
```bash
docker compose up -d --build
docker compose ps
```

### 9) Open the app in your browser
Find the VM’s **External IP** in the console.

- UI: `http://EXTERNAL_IP:8080`
- API health: `http://EXTERNAL_IP:5000/api/health`
- Employees page after login: `http://EXTERNAL_IP:8080/employees.html`

### 10) Updating the deployment
```bash
cd shivam-demo
git pull
docker compose up -d --build
```

### 11) Staying within free/trial credit (important)
- **Stop the VM** when not using it (Compute Engine → VM instances → Stop).
- If you’re done permanently, **delete**:
  - VM instance
  - Firewall rule(s) you created
  - Any disks/snapshots (if left behind)
- Set a **Budget + Alert** in Billing so you’re warned early.

---

## Option B (more “cloud-native” but can cost more): Cloud Run + Cloud SQL

If you want fully managed services:
- Deploy `server` to **Cloud Run**
- Deploy `ui` to **Cloud Run** (or Cloud Storage + Cloud CDN)
- Use **Cloud SQL (MySQL)** for the DB

This is clean, but **Cloud SQL is not free-tier** (it will consume trial credits and can become billable later). For a demo under tight cost constraints, Option A is usually better.


