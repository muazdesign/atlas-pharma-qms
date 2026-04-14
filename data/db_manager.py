"""
Atlas Pharma QMS — Database Manager
Handles SQLite connection, table initialization, and CRUD operations.

Tables:
  - products          — Master product registry (UNIQUE product_name)
  - users             — User accounts with RBAC
  - reviews           — Customer quality feedback (FK → products)
  - specs_master      — Human-readable documentation specs (FK → products, qc_checklists)
  - qc_checklists     — Operational QC checkpoint definitions (FK → products)
  - batch_records     — QC test results per batch (FK → products, qc_checklists)
  - capa_logs         — Corrective/Preventive Action logs (FK → reviews)
  - partners_directory — External lab/partner directory
  - global_chat       — Internal messaging (FK → users)
"""

import sqlite3
import hashlib
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "qms.db")

# Valid defect types (used for validation in Python; also enforced in CHECK constraint)
VALID_DEFECT_TYPES = ('Critical', 'Major', 'Minor', 'Informational')


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
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT UNIQUE NOT NULL,
            form TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

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
            product_id INTEGER REFERENCES products(id) ON DELETE RESTRICT,
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
            product_id INTEGER REFERENCES products(id) ON DELETE RESTRICT,
            form TEXT NOT NULL,
            checkpoint TEXT NOT NULL,
            sample_size TEXT,
            test_method TEXT,
            tolerance TEXT,
            pass_fail_criterion TEXT,
            defect_type TEXT CHECK(defect_type IN ('Critical', 'Major', 'Minor', 'Informational') OR defect_type IS NULL),
            checklist_id INTEGER REFERENCES qc_checklists(id)
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

        CREATE TABLE IF NOT EXISTS qc_checklists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            product_id INTEGER REFERENCES products(id) ON DELETE RESTRICT,
            form TEXT NOT NULL,
            checkpoint TEXT NOT NULL,
            sample_size TEXT NOT NULL,
            sample_count INTEGER NOT NULL,
            tolerance TEXT NOT NULL,
            unit TEXT DEFAULT '',
            tol_min REAL,
            tol_max REAL,
            test_type TEXT DEFAULT 'variable',
            test_method TEXT DEFAULT '',
            pass_fail_criterion TEXT DEFAULT '',
            defect_type TEXT DEFAULT '' CHECK(defect_type IN ('Critical', 'Major', 'Minor', 'Informational', '') OR defect_type IS NULL)
        );

        CREATE TABLE IF NOT EXISTS batch_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_number TEXT NOT NULL,
            product_name TEXT NOT NULL,
            product_id INTEGER REFERENCES products(id) ON DELETE RESTRICT,
            checklist_id INTEGER NOT NULL,
            checkpoint TEXT NOT NULL,
            individual_values TEXT NOT NULL,
            sample_count INTEGER NOT NULL,
            mean REAL NOT NULL,
            range_val REAL NOT NULL,
            tol_min REAL,
            tol_max REAL,
            status TEXT NOT NULL CHECK(status IN ('PASS', 'FAIL')),
            tested_by TEXT NOT NULL,
            tested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (checklist_id) REFERENCES qc_checklists(id)
        );

        -- Indices on FK columns
        CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews(product_id);
        CREATE INDEX IF NOT EXISTS idx_specs_product_id ON specs_master(product_id);
        CREATE INDEX IF NOT EXISTS idx_specs_checklist_id ON specs_master(checklist_id);
        CREATE INDEX IF NOT EXISTS idx_checklists_product_id ON qc_checklists(product_id);
        CREATE INDEX IF NOT EXISTS idx_batch_records_product_id ON batch_records(product_id);
    """)

    conn.commit()

    # ── Additive migrations (safe on existing DBs) ────────────────────────
    _migrate_add_columns(conn)

    conn.close()


def _migrate_add_columns(conn):
    """Add columns that may not exist on older databases."""
    _add_column_if_missing(conn, 'products', 'description', 'TEXT')
    _add_column_if_missing(conn, 'products', 'image_url', 'TEXT')
    _add_column_if_missing(conn, 'products', 'category', 'TEXT')
    _add_column_if_missing(conn, 'products', 'dosage_form', 'TEXT')
    _add_column_if_missing(conn, 'products', 'specifications', 'TEXT')
    _add_column_if_missing(conn, 'products', 'buy_link', 'TEXT')
    _add_column_if_missing(conn, 'products', 'is_active', 'INTEGER DEFAULT 1')
    _add_column_if_missing(conn, 'batch_records', 'batch_size', 'INTEGER')
    _add_column_if_missing(conn, 'batch_records', 'aql_level', 'TEXT')
    conn.commit()


def _add_column_if_missing(conn, table, column, col_type):
    """Safely add a column if it doesn't already exist."""
    cursor = conn.execute(f"PRAGMA table_info({table})")
    existing = [row[1] for row in cursor.fetchall()]
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")



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
# Product CRUD
# ---------------------------------------------------------------------------

def get_or_create_product(product_name: str, form: str = None) -> int:
    """Return product ID, creating the product if it doesn't exist."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM products WHERE product_name = ?", (product_name,)
        ).fetchone()
        if row:
            return row["id"]
        cursor = conn.execute(
            "INSERT INTO products (product_name, form) VALUES (?, ?)",
            (product_name, form),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_all_products():
    """Return all products ordered by name."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM products ORDER BY product_name").fetchall()
    conn.close()
    return rows


def get_active_products():
    """Return only active products for the public catalog."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM products WHERE is_active = 1 OR is_active IS NULL ORDER BY product_name"
    ).fetchall()
    conn.close()
    return rows


def get_product_by_id(product_id: int):
    """Return a single product by ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return row


def get_product_by_name(product_name: str):
    """Return a single product by name."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM products WHERE product_name = ?", (product_name,)
    ).fetchone()
    conn.close()
    return row


def update_product(product_id, product_name=None, form=None, description=None,
                   image_url=None, category=None, dosage_form=None,
                   specifications=None, buy_link=None, is_active=None):
    """Update an existing product. Only non-None fields are updated."""
    conn = get_connection()
    try:
        sets = []
        params = []
        if product_name is not None:
            sets.append("product_name = ?")
            params.append(product_name)
        if form is not None:
            sets.append("form = ?")
            params.append(form)
        if description is not None:
            sets.append("description = ?")
            params.append(description)
        if image_url is not None:
            sets.append("image_url = ?")
            params.append(image_url)
        if category is not None:
            sets.append("category = ?")
            params.append(category)
        if dosage_form is not None:
            sets.append("dosage_form = ?")
            params.append(dosage_form)
        if specifications is not None:
            sets.append("specifications = ?")
            params.append(specifications)
        if buy_link is not None:
            sets.append("buy_link = ?")
            params.append(buy_link)
        if is_active is not None:
            sets.append("is_active = ?")
            params.append(is_active)
        if not sets:
            return
        params.append(product_id)
        conn.execute(
            f"UPDATE products SET {', '.join(sets)} WHERE id = ?",
            params
        )
        conn.commit()
    finally:
        conn.close()


def delete_product(product_id):
    """Delete a product by ID. Soft-delete by setting is_active = 0."""
    conn = get_connection()
    try:
        conn.execute("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,))
        conn.commit()
    finally:
        conn.close()


def hard_delete_product(product_id):
    """Permanently delete a product. Use with caution."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
    finally:
        conn.close()


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
                  ai_category: str = "Pending", ai_sentiment: str = "Neutral",
                  product_id: int = None):
    """Insert a new review from the public feedback form.
    
    If product_id is not provided, it will be looked up (or created)
    from product_type for backward compatibility.
    """
    if product_id is None:
        product_id = get_or_create_product(product_type)

    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO reviews (batch_number, product_type, product_id, review_text, ai_category, ai_sentiment)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (batch_number, product_type, product_id, review_text, ai_category, ai_sentiment),
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
    """Return all specs, with optional join to products for enrichment."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT sm.*, p.product_name as p_name
        FROM specs_master sm
        LEFT JOIN products p ON sm.product_id = p.id
        ORDER BY sm.product_name, sm.checkpoint
    """).fetchall()
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


# ---------------------------------------------------------------------------
# QC Checklists CRUD
# ---------------------------------------------------------------------------

def get_distinct_qc_products():
    """Return distinct product names from qc_checklists (via products table when available)."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT DISTINCT COALESCE(p.product_name, qc.product_name) as product_name
        FROM qc_checklists qc
        LEFT JOIN products p ON qc.product_id = p.id
        ORDER BY product_name
    """).fetchall()
    conn.close()
    return [row['product_name'] for row in rows]


def get_qc_checklists_by_product(product_name):
    """Return all checklist items for a given product.
    
    Looks up by product_id first (via products table), falls back to
    free-text product_name for backward compatibility.
    """
    conn = get_connection()
    # Try product_id lookup first
    product = conn.execute(
        "SELECT id FROM products WHERE product_name = ?", (product_name,)
    ).fetchone()

    if product:
        rows = conn.execute(
            "SELECT * FROM qc_checklists WHERE product_id = ? ORDER BY id",
            (product["id"],)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM qc_checklists WHERE product_name = ? ORDER BY id",
            (product_name,)
        ).fetchall()

    conn.close()
    return rows


# ---------------------------------------------------------------------------
# Batch Records CRUD
# ---------------------------------------------------------------------------

def insert_batch_record(batch_number, product_name, checklist_id, checkpoint,
                        individual_values, sample_count, mean, range_val,
                        tol_min, tol_max, status, tested_by,
                        product_id=None):
    """Insert a QC test result for a single checkpoint in a batch.
    
    If product_id is not provided, it will be looked up from product_name.
    """
    if product_id is None:
        product_id = get_or_create_product(product_name)

    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO batch_records
               (batch_number, product_name, product_id, checklist_id, checkpoint,
                individual_values, sample_count, mean, range_val,
                tol_min, tol_max, status, tested_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (batch_number, product_name, product_id, checklist_id, checkpoint,
             individual_values, sample_count, mean, range_val,
             tol_min, tol_max, status, tested_by),
        )
        conn.commit()
    finally:
        conn.close()


def get_batch_records_by_batch(batch_number):
    """Return all QC test results for a given batch number."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT br.*, qc.tolerance, qc.unit, qc.sample_size
           FROM batch_records br
           LEFT JOIN qc_checklists qc ON br.checklist_id = qc.id
           WHERE br.batch_number = ?
           ORDER BY br.tested_at""",
        (batch_number,)
    ).fetchall()
    conn.close()
    return rows


def get_batch_records_for_spc(product_name, checkpoint):
    """Return historical mean/range data for SPC charts, ordered by batch.
    
    Uses product_id lookup (via products table) rather than free-text
    string matching for reliable filtering.
    """
    conn = get_connection()

    # Resolve product_id
    product = conn.execute(
        "SELECT id FROM products WHERE product_name = ?", (product_name,)
    ).fetchone()

    if product:
        rows = conn.execute(
            """SELECT batch_number, mean, range_val, sample_count, tol_min, tol_max, tested_at
               FROM batch_records
               WHERE product_id = ? AND checkpoint = ?
               ORDER BY tested_at ASC""",
            (product["id"], checkpoint)
        ).fetchall()
    else:
        # Fallback to text matching
        rows = conn.execute(
            """SELECT batch_number, mean, range_val, sample_count, tol_min, tol_max, tested_at
               FROM batch_records
               WHERE product_name = ? AND checkpoint = ?
               ORDER BY tested_at ASC""",
            (product_name, checkpoint)
        ).fetchall()

    conn.close()
    return rows


def get_distinct_batches(product_name):
    """Return distinct batch numbers for a given product from batch_records."""
    conn = get_connection()
    product = conn.execute(
        "SELECT id FROM products WHERE product_name = ?", (product_name,)
    ).fetchone()

    if product:
        rows = conn.execute(
            "SELECT DISTINCT batch_number FROM batch_records WHERE product_id = ? ORDER BY tested_at DESC",
            (product["id"],)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT DISTINCT batch_number FROM batch_records WHERE product_name = ? ORDER BY tested_at DESC",
            (product_name,)
        ).fetchall()

    conn.close()
    return [row['batch_number'] for row in rows]


def get_distinct_checkpoints(product_name=None):
    """Return distinct checkpoints, optionally filtered by product.
    
    Uses product_id lookup for reliable filtering.
    """
    conn = get_connection()

    if product_name:
        # Resolve product_id first
        product = conn.execute(
            "SELECT id FROM products WHERE product_name = ?", (product_name,)
        ).fetchone()

        if product:
            rows = conn.execute(
                "SELECT DISTINCT checkpoint FROM qc_checklists WHERE product_id = ? ORDER BY checkpoint",
                (product["id"],)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT DISTINCT checkpoint FROM qc_checklists WHERE product_name = ? ORDER BY checkpoint",
                (product_name,)
            ).fetchall()
    else:
        rows = conn.execute(
            "SELECT DISTINCT checkpoint FROM qc_checklists ORDER BY checkpoint"
        ).fetchall()

    conn.close()
    return [row['checkpoint'] for row in rows]


# ---------------------------------------------------------------------------
# Specs Master CRUD (Frontend editing)
# ---------------------------------------------------------------------------

def insert_spec(product_name, form, checkpoint, sample_size, test_method,
                tolerance, pass_fail, defect, product_id=None, checklist_id=None):
    """Insert a new product specification row."""
    if product_id is None:
        product_id = get_or_create_product(product_name, form)

    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO specs_master 
               (product_name, product_id, form, checkpoint, sample_size, test_method,
                tolerance, pass_fail_criterion, defect_type, checklist_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (product_name, product_id, form, checkpoint, sample_size, test_method,
             tolerance, pass_fail, defect, checklist_id),
        )
        conn.commit()
    finally:
        conn.close()


def insert_bulk_specs(product_name, form, rows):
    """Insert multiple spec rows at once (from Excel import).
    
    Now also writes to qc_checklists as the operational source of truth.
    """
    product_id = get_or_create_product(product_name, form)

    conn = get_connection()
    try:
        for r in rows:
            checkpoint = r.get('checkpoint', '')
            sample_size = r.get('sample_size', '')
            test_method = r.get('test_method', '')
            tolerance = r.get('tolerance', '')
            pass_fail = r.get('pass_fail_criterion', '')
            defect = r.get('defect_type', '')

            # Parse tolerance for tol_min / tol_max (best-effort)
            tol_min, tol_max = _parse_tolerance(tolerance)

            # Parse sample_count from sample_size text (best-effort)
            sample_count = _parse_sample_count(sample_size)

            # 1) Insert into qc_checklists (operational table)
            cursor = conn.execute(
                """INSERT INTO qc_checklists
                   (product_name, product_id, form, checkpoint, sample_size,
                    sample_count, tolerance, unit, tol_min, tol_max,
                    test_type, test_method, pass_fail_criterion, defect_type)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (product_name, product_id, form, checkpoint, sample_size,
                 sample_count, tolerance, '', tol_min, tol_max,
                 'variable', test_method, pass_fail, defect),
            )
            checklist_id = cursor.lastrowid

            # 2) Insert into specs_master (documentation table, linked)
            conn.execute(
                """INSERT INTO specs_master
                   (product_name, product_id, form, checkpoint, sample_size,
                    test_method, tolerance, pass_fail_criterion, defect_type, checklist_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (product_name, product_id, form, checkpoint, sample_size,
                 test_method, tolerance, pass_fail, defect, checklist_id),
            )

        conn.commit()
    finally:
        conn.close()


def _parse_tolerance(tolerance_str):
    """Best-effort parse of tolerance text into (tol_min, tol_max) floats."""
    import re
    if not tolerance_str:
        return None, None
    
    # Pattern: "522.5 – 577.5" or "5 - 10" or "98 – 102"
    range_match = re.search(r'([\d.]+)\s*[–—-]\s*([\d.]+)', tolerance_str)
    if range_match:
        try:
            return float(range_match.group(1)), float(range_match.group(2))
        except ValueError:
            pass
    
    # Pattern: "≤ 15" or "<= 15"
    lte_match = re.search(r'[≤<]=?\s*([\d.]+)', tolerance_str)
    if lte_match:
        try:
            return 0.0, float(lte_match.group(1))
        except ValueError:
            pass
    
    # Pattern: "≥ 80" or ">= 80"
    gte_match = re.search(r'[≥>]=?\s*([\d.]+)', tolerance_str)
    if gte_match:
        try:
            return float(gte_match.group(1)), None
        except ValueError:
            pass
    
    # Pattern: "550 ± 5%" → 522.5 – 577.5
    pm_match = re.search(r'([\d.]+)\s*±\s*([\d.]+)(%?)', tolerance_str)
    if pm_match:
        try:
            center = float(pm_match.group(1))
            delta = float(pm_match.group(2))
            if pm_match.group(3) == '%':
                delta = center * delta / 100
            return round(center - delta, 2), round(center + delta, 2)
        except ValueError:
            pass
    
    return None, None


def _parse_sample_count(sample_size_str):
    """Best-effort parse of sample size text into an integer count."""
    import re
    if not sample_size_str:
        return 1
    
    # "10 tablets / batch" → 10
    match = re.search(r'(\d+)', sample_size_str)
    if match:
        return int(match.group(1))
    
    # "Composite sample" or "100%" → default to 1
    return 1


def delete_spec(spec_id):
    """Delete a specification by its ID."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM specs_master WHERE id = ?", (spec_id,))
        conn.commit()
    finally:
        conn.close()


def update_spec(spec_id, product_name, form, checkpoint, sample_size,
                test_method, tolerance, pass_fail, defect):
    """Update an existing specification."""
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE specs_master
               SET product_name = ?, form = ?, checkpoint = ?, sample_size = ?,
                   test_method = ?, tolerance = ?, pass_fail_criterion = ?, defect_type = ?
               WHERE id = ?""",
            (product_name, form, checkpoint, sample_size, test_method, tolerance, pass_fail, defect, spec_id),
        )
        conn.commit()
    finally:
        conn.close()
