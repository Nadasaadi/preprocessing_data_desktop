import mysql.connector
import hashlib

# --- Configuration de connexion MySQL ---
DB_CONFIG = {
    "host": "localhost",
    "user": "root",           # ⚠️ adapte selon ton Workbench
    "password": "nadasaadi2003*",
    "database": "users_dwh1"
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def hash_password(password):
    """Retourne le hash SHA-256 du mot de passe"""
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
        (username, hash_password(password))
    )
    conn.commit()
    cur.close()
    conn.close()

def user_exists(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

def verify_user(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0] == hash_password(password)
    return False
