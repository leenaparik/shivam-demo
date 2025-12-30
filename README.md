## What you’re building

Three Docker containers:

- **UI**: Nginx serving a simple HTML/JS page (register + login).
- **Server**: Python (Flask) API that registers/logs in users and reads/writes MySQL.
- **Database**: MySQL storing user profile + password hash + encrypted SSN.

## Prereqs

- Docker Desktop running (Windows)
- Docker Compose (comes with Docker Desktop)

## Configure environment variables

This repo includes `env.example`. Create a local `.env` next to `docker-compose.yml`:

- Copy `env.example` → `.env`
- Fill `SSN_KEY` (required). Generate it on your machine:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

If you don’t create a `.env`, the app will still run (it uses a built-in demo `SSN_KEY`), but you should set your own for anything beyond a demo.

## Start the app (3 containers)

From the repo folder:

```bash
docker compose up --build
```

Then open:

- `http://localhost:8080` (UI)

The API is at:

- `http://localhost:5000/api/health`

## Stop / reset

Stop:

```bash
docker compose down
```

Stop + delete DB data:

```bash
docker compose down -v
```

## Notes (important)

- **Passwords are never stored in plain text** (they’re hashed).
- **SSN is encrypted at rest** using the `SSN_KEY` you provide (the UI/API only shows last-4).


