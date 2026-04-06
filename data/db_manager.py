"""
Atlas Pharma QMS — Database Manager
Handles SQLite connection, table initialization, and CRUD operations.
"""

import sqlite3
import hashlib
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "qms.db")


def get_connection():
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('Admin', 'Quality Manager', 'Executive'))
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_number TEXT NOT NULL,
            product_type TEXT NOT NULL,
            review_text TEXT NOT NULL,
            ai_category TEXT DEFAULT 'Pending' CHECK(ai_category IN ('Critical', 'Major', 'Minor', 'Pending')),
            ai_sentiment TEXT DEFAULT 'Neutral',
            status TEXT DEFAULT 'Open' CHECK(status IN ('Open', 'Claimed', 'Resolved')),
            claimed_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS specs_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            form TEXT NOT NULL,
            parameter TEXT NOT NULL,
            specification TEXT NOT NULL,
            test_method TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS partners_directory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            institution_name TEXT NOT NULL,
            type TEXT NOT NULL,
            standards TEXT,
            contact_info TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS capa_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL,
            root_cause TEXT NOT NULL,
            corrective_action TEXT NOT NULL,
            preventive_action TEXT NOT NULL,
            manager_assigned TEXT NOT NULL,
            resolved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (review_id) REFERENCES reviews(id)
        );
        CREATE TABLE IF NOT EXISTS global_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Password Helpers
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Return a SHA-256 hash of the password."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Check a plain-text password against a stored hash."""
    return hash_password(password) == password_hash


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------

def get_user(username: str):
    """Fetch a user row by username."""
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user


def get_all_users():
    """Return all users ordered by role."""
    conn = get_connection()
    rows = conn.execute("SELECT id, username, full_name, role FROM users ORDER BY role, full_name").fetchall()
    conn.close()
    return rows


def delete_user(user_id: int):
    """Delete a user by ID."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


def create_user(username: str, password: str, full_name: str, role: str):
    """Insert a new user. Ignores if username already exists."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            (username, hash_password(password), full_name, role),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Global Chat CRUD
# ---------------------------------------------------------------------------

def insert_chat_message(user_id: int, message: str):
    """Insert a new global chat message."""
    conn = get_connection()
    try:
        conn.execute("INSERT INTO global_chat (user_id, message) VALUES (?, ?)", (user_id, message))
        conn.commit()
    finally:
        conn.close()


def get_chat_messages(limit: int = 50):
    """Return recent chat messages joined with user info."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT c.id, c.message, c.timestamp as created_at, u.full_name, u.role
        FROM global_chat c
        JOIN users u ON c.user_id = u.id
        ORDER BY c.timestamp ASC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# Review CRUD
# ---------------------------------------------------------------------------

def insert_review(batch_number: str, product_type: str, review_text: str,
                  ai_category: str = "Pending", ai_sentiment: str = "Neutral"):
    """Insert a new review from the public feedback form."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO reviews (batch_number, product_type, review_text, ai_category, ai_sentiment)
               VALUES (?, ?, ?, ?, ?)""",
            (batch_number, product_type, review_text, ai_category, ai_sentiment),
        )
        conn.commit()
    finally:
        conn.close()


def get_all_reviews():
    """Return all reviews ordered by newest first."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM reviews ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows


def get_reviews_by_status(status: str):
    """Return reviews filtered by status."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM reviews WHERE status = ? ORDER BY created_at DESC", (status,)).fetchall()
    conn.close()
    return rows


def get_review_by_id(review_id: int):
    """Return a single review by its ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()
    conn.close()
    return row


def claim_review(review_id: int, claimed_by: str):
    """Mark a review as Claimed by a quality manager."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE reviews SET status = 'Claimed', claimed_by = ? WHERE id = ?",
            (claimed_by, review_id),
        )
        conn.commit()
    finally:
        conn.close()


def resolve_review(review_id: int):
    """Mark a review as Resolved."""
    conn = get_connection()
    try:
        conn.execute("UPDATE reviews SET status = 'Resolved' WHERE id = ?", (review_id,))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CAPA CRUD
# ---------------------------------------------------------------------------

def insert_capa(review_id: int, root_cause: str, corrective_action: str,
                preventive_action: str, manager_assigned: str):
    """Log a CAPA resolution and mark the linked review as Resolved."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO capa_logs (review_id, root_cause, corrective_action, preventive_action, manager_assigned)
               VALUES (?, ?, ?, ?, ?)""",
            (review_id, root_cause, corrective_action, preventive_action, manager_assigned),
        )
        conn.execute("UPDATE reviews SET status = 'Resolved' WHERE id = ?", (review_id,))
        conn.commit()
    finally:
        conn.close()


def get_all_capa_logs():
    """Return all CAPA logs with joined review info."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT c.*, r.batch_number, r.product_type, r.review_text, r.ai_category
        FROM capa_logs c
        JOIN reviews r ON c.review_id = r.id
        ORDER BY c.resolved_at DESC
    """).fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# Specs & Partners CRUD
# ---------------------------------------------------------------------------

def get_all_specs():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM specs_master ORDER BY product_name, parameter").fetchall()
    conn.close()
    return rows


def get_all_partners():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM partners_directory ORDER BY institution_name").fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# Dashboard Aggregations
# ---------------------------------------------------------------------------

def get_category_counts():
    """Return counts per AI category."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT ai_category, COUNT(*) as cnt FROM reviews GROUP BY ai_category"
    ).fetchall()
    conn.close()
    return {row["ai_category"]: row["cnt"] for row in rows}


def get_status_counts():
    """Return counts per status."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT status, COUNT(*) as cnt FROM reviews GROUP BY status"
    ).fetchall()
    conn.close()
    return {row["status"]: row["cnt"] for row in rows}


def get_monthly_trend():
    """Return monthly counts of reviews."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as cnt
        FROM reviews
        GROUP BY month
        ORDER BY month
    """).fetchall()
    conn.close()
    return rows


def get_live_operations():
    """Return all Quality Managers and any tickets they've claimed for live tracking."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT u.id, u.full_name, u.role, r.id as review_id, r.status
        FROM users u
        LEFT JOIN reviews r ON u.full_name = r.claimed_by AND r.status = 'Claimed'
        WHERE u.role = 'Quality Manager'
        ORDER BY u.full_name
    """).fetchall()
    conn.close()
    return rows
