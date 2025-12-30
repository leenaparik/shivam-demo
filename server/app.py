import os
import time
import json
import urllib.error
import urllib.parse
import urllib.request

import mysql.connector
from cryptography.fernet import Fernet, InvalidToken
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash


def required_env(name: str) -> str:
    value = os.getenv(name, "")
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


DB_HOST = os.getenv("DB_HOST", "mysql")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "appdb")
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "apppass")

UI_ORIGIN = os.getenv("UI_ORIGIN", "http://localhost:8080")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

CORS(app, resources={r"/api/*": {"origins": [UI_ORIGIN]}}, supports_credentials=True)


def get_fernet() -> Fernet:
    key = required_env("SSN_KEY")
    return Fernet(key.encode("utf-8"))


def get_db_connection():
    # Retry because MySQL may take a moment to accept connections even after container start.
    last_err = None
    for _ in range(40):
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                autocommit=True,
            )
            return conn
        except mysql.connector.Error as e:
            last_err = e
            time.sleep(1)
    raise last_err


def ensure_schema():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
              id INT AUTO_INCREMENT PRIMARY KEY,
              username VARCHAR(128) NOT NULL UNIQUE,
              first_name VARCHAR(128) NOT NULL,
              last_name VARCHAR(128) NOT NULL,
              address VARCHAR(255) NOT NULL,
              ssn_enc TEXT NOT NULL,
              password_hash VARCHAR(255) NOT NULL,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.close()
    finally:
        conn.close()


@app.get("/api/health")
def health():
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({"ok": True, "db": "up"})
    except Exception as e:
        return jsonify({"ok": False, "db": "down", "error": str(e)}), 500


def _parse_number_param(*names: str) -> float | None:
    for name in names:
        raw = request.args.get(name, None)
        if raw is None:
            continue
        raw = raw.strip()
        if raw == "":
            continue
        try:
            return float(raw)
        except ValueError:
            raise ValueError(f"Query parameter '{name}' must be a number.")
    return None


@app.get("/api/add")
def add_two_numbers():
    """
    Add two numbers passed as query parameters.

    Examples:
      /api/add?a=1&b=2
      /api/add?x=3.5&y=4
      /api/add?num1=10&num2=20
    """
    try:
        a = _parse_number_param("a", "x", "num1")
        b = _parse_number_param("b", "y", "num2")
        if a is None or b is None:
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "Provide two numbers as query params, e.g. /api/add?a=1&b=2",
                    }
                ),
                400,
            )

        result = a + b
        # If the result is an integer value, return it as int (nicer JSON).
        result_json = int(result) if result.is_integer() else result
        return jsonify({"ok": True, "a": a, "b": b, "sum": result_json})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


def _fetch_json(url: str, timeout_s: int = 10):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "shivam-demo/1.0",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        body = resp.read().decode("utf-8", "replace")
        return resp.status, json.loads(body)


@app.get("/api/employees")
def employees():
    """
    Fetch employees from the upstream API and return the JSON response.
    Upstream: https://boringapi.com/api/v1/employees

    Supports passing through query params, e.g.:
      /api/employees?page=2
    """
    upstream_base = "https://boringapi.com/api/v1/employees"
    query = urllib.parse.urlencode(request.args, doseq=True)
    upstream_url = f"{upstream_base}?{query}" if query else upstream_base

    try:
        status, data = _fetch_json(upstream_url, timeout_s=10)
        return jsonify({"ok": True, "upstream_status": status, "data": data})
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", "replace")
            return jsonify({"ok": False, "error": "Upstream returned error", "status": e.code, "body": body}), 502
        except Exception:
            return jsonify({"ok": False, "error": "Upstream returned error", "status": e.code}), 502
    except urllib.error.URLError as e:
        return jsonify({"ok": False, "error": "Upstream unreachable", "detail": str(e)}), 502
    except Exception as e:
        return jsonify({"ok": False, "error": "Unexpected error", "detail": str(e)}), 500


@app.post("/api/register")
def register():
    payload = request.get_json(force=True, silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    first_name = (payload.get("first_name") or "").strip()
    last_name = (payload.get("last_name") or "").strip()
    address = (payload.get("address") or "").strip()
    ssn = (payload.get("ssn") or "").strip()

    if not all([username, password, first_name, last_name, address, ssn]):
        return jsonify({"ok": False, "error": "All fields are required."}), 400

    if len(username) < 3:
        return jsonify({"ok": False, "error": "Username must be at least 3 characters."}), 400

    if len(password) < 8:
        return jsonify({"ok": False, "error": "Password must be at least 8 characters."}), 400

    f = get_fernet()
    ssn_enc = f.encrypt(ssn.encode("utf-8")).decode("utf-8")
    pw_hash = generate_password_hash(password)

    conn = get_db_connection()
    try:
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(
                """
                INSERT INTO users (username, first_name, last_name, address, ssn_enc, password_hash)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (username, first_name, last_name, address, ssn_enc, pw_hash),
            )
        except mysql.connector.IntegrityError:
            return jsonify({"ok": False, "error": "Username already exists."}), 409

        user_id = cur.lastrowid
        session["user_id"] = user_id
        session["username"] = username
        return jsonify({"ok": True, "user_id": user_id, "username": username})
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()


@app.post("/api/login")
def login():
    payload = request.get_json(force=True, silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if not username or not password:
        return jsonify({"ok": False, "error": "Username and password are required."}), 400

    conn = get_db_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, username, password_hash FROM users WHERE username=%s", (username,))
        row = cur.fetchone()
        if not row or not check_password_hash(row["password_hash"], password):
            return jsonify({"ok": False, "error": "Invalid username or password."}), 401

        session["user_id"] = row["id"]
        session["username"] = row["username"]
        return jsonify({"ok": True})
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/me")
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in."}), 401

    conn = get_db_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, username, first_name, last_name, address, ssn_enc, created_at
            FROM users
            WHERE id=%s
            """,
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            session.clear()
            return jsonify({"ok": False, "error": "User not found."}), 404

        # Decrypt SSN only to show last-4 (avoid returning full SSN).
        ssn_last4 = "****"
        try:
            f = get_fernet()
            ssn_plain = f.decrypt(row["ssn_enc"].encode("utf-8")).decode("utf-8")
            ssn_last4 = ssn_plain[-4:] if len(ssn_plain) >= 4 else ssn_plain
        except (InvalidToken, Exception):
            ssn_last4 = "****"

        return jsonify(
            {
                "ok": True,
                "user": {
                    "id": row["id"],
                    "username": row["username"],
                    "first_name": row["first_name"],
                    "last_name": row["last_name"],
                    "address": row["address"],
                    "ssn_last4": ssn_last4,
                    "created_at": str(row["created_at"]),
                },
            }
        )
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()


if __name__ == "__main__":
    # Fail fast if encryption key is missing/malformed.
    # (Without this, register/me would error later in confusing ways.)
    get_fernet()
    ensure_schema()
    app.run(host="0.0.0.0", port=5000, debug=False)


