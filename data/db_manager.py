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
            checklist_id INTEGER,
            checkpoint TEXT NOT NULL,
            individual_values TEXT NOT NULL,
            sample_count INTEGER NOT NULL,
            mean REAL,
            range_val REAL,
            tol_min REAL,
            tol_max REAL,
            status TEXT NOT NULL CHECK(status IN ('PASS', 'FAIL')),
            tested_by TEXT NOT NULL,
            tested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (checklist_id) REFERENCES qc_checklists(id)
        );

        -- ── New Stage-Based Manufacturing Tables ──────────────────────────

        CREATE TABLE IF NOT EXISTS production_stages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stage_code TEXT UNIQUE NOT NULL,
            stage_name TEXT NOT NULL,
            layer TEXT NOT NULL CHECK(layer IN ('IQC', 'IPQC', 'FQC')),
            product_form TEXT CHECK(product_form IN ('Tablet', 'Syrup') OR product_form IS NULL),
            sequence_order INTEGER NOT NULL,
            equipment_json TEXT DEFAULT '[]'
        );

        CREATE TABLE IF NOT EXISTS stage_checkpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stage_id INTEGER NOT NULL,
            section TEXT DEFAULT '',
            checkpoint_no TEXT NOT NULL,
            checkpoint_name TEXT NOT NULL,
            sample_size TEXT DEFAULT '',
            sample_count INTEGER DEFAULT 1,
            instruction TEXT DEFAULT '',
            tolerance TEXT DEFAULT '',
            unit TEXT DEFAULT '',
            tol_min REAL,
            tol_max REAL,
            frequency TEXT DEFAULT '',
            defect_type TEXT DEFAULT '',
            test_type TEXT DEFAULT 'variable',
            FOREIGN KEY (stage_id) REFERENCES production_stages(id)
        );

        CREATE TABLE IF NOT EXISTS material_lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_type TEXT NOT NULL CHECK(material_type IN ('API', 'Excipient', 'Packaging')),
            material_name TEXT NOT NULL,
            lot_number TEXT UNIQUE NOT NULL,
            supplier TEXT DEFAULT '',
            received_date TEXT,
            expiry_date TEXT,
            quantity REAL,
            unit TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Quarantine' CHECK(status IN ('Quarantine', 'Released', 'Rejected')),
            released_by TEXT,
            released_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_number TEXT UNIQUE NOT NULL,
            product_id INTEGER NOT NULL,
            batch_size INTEGER,
            status TEXT NOT NULL DEFAULT 'Created' CHECK(status IN ('Created', 'In-Progress', 'Pending-Release', 'Released', 'Rejected')),
            current_stage_id INTEGER,
            created_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            released_by TEXT,
            released_at TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (current_stage_id) REFERENCES production_stages(id)
        );

        CREATE TABLE IF NOT EXISTS batch_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER NOT NULL,
            material_lot_id INTEGER NOT NULL,
            quantity_used REAL,
            unit TEXT DEFAULT '',
            FOREIGN KEY (batch_id) REFERENCES batches(id),
            FOREIGN KEY (material_lot_id) REFERENCES material_lots(id)
        );

        CREATE TABLE IF NOT EXISTS batch_stage_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER NOT NULL,
            stage_id INTEGER NOT NULL,
            verdict TEXT NOT NULL CHECK(verdict IN ('PASS', 'FAIL', 'IN_PROGRESS')),
            notes TEXT DEFAULT '',
            signed_by TEXT,
            signed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (batch_id) REFERENCES batches(id),
            FOREIGN KEY (stage_id) REFERENCES production_stages(id),
            UNIQUE(batch_id, stage_id)
        );

        -- Indices on FK columns
        CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews(product_id);
        CREATE INDEX IF NOT EXISTS idx_specs_product_id ON specs_master(product_id);
        CREATE INDEX IF NOT EXISTS idx_specs_checklist_id ON specs_master(checklist_id);
        CREATE INDEX IF NOT EXISTS idx_checklists_product_id ON qc_checklists(product_id);
        CREATE INDEX IF NOT EXISTS idx_batch_records_product_id ON batch_records(product_id);
        CREATE INDEX IF NOT EXISTS idx_stage_checkpoints_stage_id ON stage_checkpoints(stage_id);
        CREATE INDEX IF NOT EXISTS idx_batches_product_id ON batches(product_id);
        CREATE INDEX IF NOT EXISTS idx_batches_current_stage ON batches(current_stage_id);
        CREATE INDEX IF NOT EXISTS idx_batch_materials_batch ON batch_materials(batch_id);
        CREATE INDEX IF NOT EXISTS idx_batch_materials_lot ON batch_materials(material_lot_id);
        CREATE INDEX IF NOT EXISTS idx_batch_stage_results_batch ON batch_stage_results(batch_id);
        CREATE INDEX IF NOT EXISTS idx_batch_stage_results_stage ON batch_stage_results(stage_id);
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
    _add_column_if_missing(conn, 'batch_records', 'batch_id', 'INTEGER REFERENCES batches(id)')
    _add_column_if_missing(conn, 'batch_records', 'stage_id', 'INTEGER REFERENCES production_stages(id)')
    _add_column_if_missing(conn, 'capa_logs', 'batch_id', 'INTEGER')
    _add_column_if_missing(conn, 'capa_logs', 'stage_id', 'INTEGER')
    _add_column_if_missing(conn, 'capa_logs', 'source_type', "TEXT DEFAULT 'complaint'")
    _add_column_if_missing(conn, 'stage_checkpoints', 'result_type', "TEXT DEFAULT 'numeric'")
    _add_column_if_missing(conn, 'stage_checkpoints', 'source', "TEXT DEFAULT 'Excel'")
    _add_column_if_missing(conn, 'stage_checkpoints', 'is_active', 'INTEGER DEFAULT 1')
    _add_column_if_missing(conn, 'stage_checkpoints', 'updated_at', 'TIMESTAMP')
    _add_column_if_missing(conn, 'stage_checkpoints', 'updated_by', 'TEXT')
    _add_column_if_missing(conn, 'batch_records', 'sample_number', 'INTEGER DEFAULT 1')

    # Audit log for checkpoint library edits (GMP traceability)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stage_checkpoints_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checkpoint_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            field_changed TEXT,
            old_value TEXT,
            new_value TEXT,
            changed_by TEXT NOT NULL,
            reason TEXT DEFAULT '',
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (checkpoint_id) REFERENCES stage_checkpoints(id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sc_audit_cp ON stage_checkpoints_audit(checkpoint_id)")

    _relax_batch_records_constraints(conn)
    _backfill_tolerance_bounds(conn)
    conn.commit()


# ─── Tolerance Parsing ─────────────────────────────────────────────────────
import re as _re

def parse_tolerance(tol_text):
    """Parse a tolerance text string into (tol_min, tol_max) float bounds.

    Returns (None, None) when it cannot extract numeric bounds.

    Examples:
        "98.0 - 101.5 %"          -> (98.0, 101.5)
        "<= 0.5 %"                 -> (None, 0.5)
        ">= 80 %"                  -> (80.0, None)
        "600 mg +/- 5 %"           -> (570.0, 630.0)
        "14.0 mm +/- 5 %"          -> (13.3, 14.7)
        "250 um +/- 10 um"         -> (240.0, 260.0)
        "Target weight gain: 2 - 4 % of core weight" -> (2.0, 4.0)
        "Per approved spec"        -> (None, None)
        "Hausner ratio <= 1.25 (good flow)" -> (None, 1.25)
    """
    if not tol_text:
        return (None, None)
    t = str(tol_text).strip()
    if not _re.search(r'\d', t):
        return (None, None)

    # 1) "+/-" or "±" pattern  (center +/- delta [%])
    m = _re.search(r'([\d.]+)\s*[A-Za-z/²]*\s*(?:\+/-|±)\s*([\d.]+)\s*(%)?', t)
    if m:
        try:
            center = float(m.group(1))
            delta = float(m.group(2))
            is_pct = m.group(3) == '%'
            if is_pct:
                lo = round(center * (1 - delta / 100.0), 4)
                hi = round(center * (1 + delta / 100.0), 4)
            else:
                lo = round(center - delta, 4)
                hi = round(center + delta, 4)
            return (lo, hi)
        except ValueError:
            pass

    # 2a) "+X.Y to +A.B" signed range (for rotation etc.)
    m = _re.search(r'([+-]?[\d.]+)\s+to\s+([+-]?[\d.]+)', t, _re.IGNORECASE)
    if m:
        try:
            lo = float(m.group(1))
            hi = float(m.group(2))
            if lo <= hi:
                return (lo, hi)
        except ValueError:
            pass

    # 2b) "X - Y" range pattern (X <= Y)
    for rm in _re.finditer(r'(?<![\d.])([\d.]+)\s*[-–]\s*([\d.]+)(?![\d.])', t):
        try:
            lo = float(rm.group(1))
            hi = float(rm.group(2))
            if lo <= hi:
                return (lo, hi)
        except ValueError:
            continue

    # 3) "<= X" or "< X"  upper bound only
    m = _re.search(r'<=?\s*([\d.]+)', t)
    if m:
        try:
            return (None, float(m.group(1)))
        except ValueError:
            pass

    # 4) ">= X" or "> X"  lower bound only
    m = _re.search(r'>=?\s*([\d.]+)', t)
    if m:
        try:
            return (float(m.group(1)), None)
        except ValueError:
            pass

    return (None, None)


def _backfill_tolerance_bounds(conn):
    """Parse tolerance text for stage_checkpoints & qc_checklists where
    tol_min / tol_max are NULL. Idempotent — safe to run every startup."""
    # stage_checkpoints (numeric result_type only)
    rows = conn.execute(
        "SELECT id, tolerance FROM stage_checkpoints "
        "WHERE (tol_min IS NULL AND tol_max IS NULL) "
        "AND COALESCE(result_type,'numeric') = 'numeric' "
        "AND tolerance IS NOT NULL AND tolerance != ''"
    ).fetchall()
    for r in rows:
        lo, hi = parse_tolerance(r['tolerance'])
        if lo is not None or hi is not None:
            conn.execute(
                "UPDATE stage_checkpoints SET tol_min = ?, tol_max = ? WHERE id = ?",
                (lo, hi, r['id'])
            )

    # qc_checklists (legacy)
    try:
        rows = conn.execute(
            "SELECT id, tolerance FROM qc_checklists "
            "WHERE tol_min IS NULL AND tol_max IS NULL "
            "AND tolerance IS NOT NULL AND tolerance != ''"
        ).fetchall()
        for r in rows:
            lo, hi = parse_tolerance(r['tolerance'])
            if lo is not None or hi is not None:
                conn.execute(
                    "UPDATE qc_checklists SET tol_min = ?, tol_max = ? WHERE id = ?",
                    (lo, hi, r['id'])
                )
    except sqlite3.OperationalError:
        pass  # qc_checklists may not have tol_min/tol_max on very old DBs


def _relax_batch_records_constraints(conn):
    """Recreate batch_records without NOT NULL on checklist_id/mean/range_val.

    Stage-based QC entries don't have a legacy checklist_id, and pass/fail
    checkpoints have no numeric mean/range.  Run this idempotently by checking
    whether checklist_id already allows NULLs.
    """
    info = {row[1]: row[3] for row in conn.execute("PRAGMA table_info(batch_records)").fetchall()}
    # row[3] is 'notnull' flag — 1 means NOT NULL
    if info.get('checklist_id', 1) == 0:
        return  # already relaxed

    conn.executescript("""
        PRAGMA foreign_keys = OFF;

        CREATE TABLE IF NOT EXISTS batch_records_new (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_number     TEXT NOT NULL,
            product_name     TEXT NOT NULL,
            product_id       INTEGER REFERENCES products(id) ON DELETE RESTRICT,
            checklist_id     INTEGER,
            checkpoint       TEXT NOT NULL,
            individual_values TEXT NOT NULL,
            sample_count     INTEGER NOT NULL,
            mean             REAL,
            range_val        REAL,
            tol_min          REAL,
            tol_max          REAL,
            status           TEXT NOT NULL CHECK(status IN ('PASS','FAIL')),
            tested_by        TEXT NOT NULL,
            tested_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            batch_size       INTEGER,
            aql_level        TEXT,
            batch_id         INTEGER,
            stage_id         INTEGER,
            sample_number    INTEGER DEFAULT 1
        );

        INSERT INTO batch_records_new
            SELECT id, batch_number, product_name, product_id, checklist_id,
                   checkpoint, individual_values, sample_count, mean, range_val,
                   tol_min, tol_max, status, tested_by, tested_at,
                   batch_size, aql_level, batch_id, stage_id,
                   COALESCE(sample_number, 1)
            FROM batch_records;

        DROP TABLE batch_records;

        ALTER TABLE batch_records_new RENAME TO batch_records;

        PRAGMA foreign_keys = ON;
    """)


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
                        product_id=None, batch_id=None, stage_id=None,
                        batch_size=None, aql_level=None):
    """Insert a QC test result for a single checkpoint in a batch.

    If product_id is not provided, it will be looked up from product_name.
    batch_id, stage_id, batch_size, aql_level are optional for stage-based entry.
    """
    if product_id is None:
        product_id = get_or_create_product(product_name)

    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO batch_records
               (batch_number, product_name, product_id, checklist_id, checkpoint,
                individual_values, sample_count, mean, range_val,
                tol_min, tol_max, status, tested_by,
                batch_id, stage_id, batch_size, aql_level)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (batch_number, product_name, product_id, checklist_id, checkpoint,
             individual_values, sample_count, mean, range_val,
             tol_min, tol_max, status, tested_by,
             batch_id, stage_id, batch_size, aql_level),
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


def get_batch_records_for_spc(product_name, checkpoint, stage_id=None):
    """Return historical mean/range data for SPC charts, ordered by batch.

    Uses product_id lookup (via products table) rather than free-text
    string matching for reliable filtering. Optionally filter by stage_id.
    """
    conn = get_connection()

    # Resolve product_id
    product = conn.execute(
        "SELECT id FROM products WHERE product_name = ?", (product_name,)
    ).fetchone()

    stage_clause = "AND stage_id = ?" if stage_id is not None else ""
    stage_param = (stage_id,) if stage_id is not None else ()

    if product:
        rows = conn.execute(
            f"""SELECT batch_number, mean, range_val, sample_count, tol_min, tol_max,
                       individual_values, status, tested_at
               FROM batch_records
               WHERE product_id = ? AND checkpoint = ? {stage_clause}
               ORDER BY tested_at ASC""",
            (product["id"], checkpoint) + stage_param
        ).fetchall()
    else:
        # Fallback to text matching
        rows = conn.execute(
            f"""SELECT batch_number, mean, range_val, sample_count, tol_min, tol_max,
                       individual_values, status, tested_at
               FROM batch_records
               WHERE product_name = ? AND checkpoint = ? {stage_clause}
               ORDER BY tested_at ASC""",
            (product_name, checkpoint) + stage_param
        ).fetchall()

    conn.close()
    return rows


def get_distinct_batches(product_name):
    """Return distinct batch numbers for a given product.

    Prefers production batches from the `batches` table (current GMP pipeline)
    and then appends any legacy batch_records batches that aren't already
    listed, ordered most-recent-first.
    """
    conn = get_connection()
    product = conn.execute(
        "SELECT id FROM products WHERE product_name = ?", (product_name,)
    ).fetchone()

    if not product:
        rows = conn.execute(
            "SELECT DISTINCT batch_number FROM batch_records WHERE product_name = ? ORDER BY tested_at DESC",
            (product_name,)
        ).fetchall()
        conn.close()
        return [row['batch_number'] for row in rows]

    # 1) Current production batches
    gmp_rows = conn.execute(
        "SELECT batch_number FROM batches WHERE product_id = ? ORDER BY created_at DESC",
        (product["id"],)
    ).fetchall()
    gmp_batches = [r['batch_number'] for r in gmp_rows]
    seen = set(gmp_batches)

    # 2) Legacy batches with recorded QC data that aren't already in the batches table
    legacy_rows = conn.execute(
        "SELECT DISTINCT batch_number, MAX(tested_at) as last_test "
        "FROM batch_records WHERE product_id = ? GROUP BY batch_number "
        "ORDER BY last_test DESC",
        (product["id"],)
    ).fetchall()
    legacy_batches = [r['batch_number'] for r in legacy_rows if r['batch_number'] not in seen]

    conn.close()
    return gmp_batches + legacy_batches


def get_distinct_checkpoints(product_name=None, stage_id=None):
    """Return distinct checkpoints, optionally filtered by product and/or stage.

    When stage_id is provided, returns checkpoint names defined in that stage's
    stage_checkpoints table (ordered by checkpoint_no).
    Otherwise falls back to qc_checklists.
    """
    conn = get_connection()

    if stage_id is not None:
        rows = conn.execute(
            "SELECT DISTINCT checkpoint_name FROM stage_checkpoints WHERE stage_id = ? ORDER BY checkpoint_no",
            (stage_id,)
        ).fetchall()
        conn.close()
        return [row['checkpoint_name'] for row in rows]

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


# ===========================================================================
# Production Stages & Stage Checkpoints
# ===========================================================================

def get_all_stages(layer=None, product_form=None):
    """Return production stages, optionally filtered by layer and/or product_form."""
    conn = get_connection()
    query = "SELECT * FROM production_stages WHERE 1=1"
    params = []
    if layer:
        query += " AND layer = ?"
        params.append(layer)
    if product_form:
        query += " AND (product_form = ? OR product_form IS NULL)"
        params.append(product_form)
    query += " ORDER BY sequence_order"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_stage_by_code(stage_code):
    """Return a single stage by its code (e.g., 'IPQC-T-02')."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM production_stages WHERE stage_code = ?", (stage_code,)
    ).fetchone()
    conn.close()
    return row


def get_stage_by_id(stage_id):
    """Return a single stage by its ID."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM production_stages WHERE id = ?", (stage_id,)
    ).fetchone()
    conn.close()
    return row


def get_checkpoints_by_stage(stage_id):
    """Return all checkpoints for a given stage, ordered by checkpoint_no."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM stage_checkpoints WHERE stage_id = ? ORDER BY id",
        (stage_id,)
    ).fetchall()
    conn.close()
    return rows


def get_checkpoint_by_id(checkpoint_id):
    """Return a single stage_checkpoint row by ID."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM stage_checkpoints WHERE id = ?", (checkpoint_id,)
    ).fetchone()
    conn.close()
    return row


def get_stages_for_product(product_id):
    """Return the ordered pipeline of stages for a product's form (Tablet/Syrup).
    IQC stages (product_form IS NULL) are included for all products.
    """
    conn = get_connection()
    product = conn.execute("SELECT form FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        conn.close()
        return []
    form = product['form']
    rows = conn.execute(
        """SELECT * FROM production_stages
           WHERE product_form = ? OR product_form IS NULL
           ORDER BY sequence_order""",
        (form,)
    ).fetchall()
    conn.close()
    return rows


# ===========================================================================
# Material Lots
# ===========================================================================

def create_material_lot(material_type, material_name, lot_number, supplier='',
                        received_date=None, expiry_date=None, quantity=None, unit=''):
    """Create a new material lot in Quarantine status."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO material_lots
               (material_type, material_name, lot_number, supplier,
                received_date, expiry_date, quantity, unit)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (material_type, material_name, lot_number, supplier,
             received_date, expiry_date, quantity, unit),
        )
        conn.commit()
    finally:
        conn.close()


def get_all_material_lots(status=None, material_type=None):
    """Return material lots, optionally filtered."""
    conn = get_connection()
    query = "SELECT * FROM material_lots WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if material_type:
        query += " AND material_type = ?"
        params.append(material_type)
    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_material_lot_by_id(lot_id):
    """Return a single material lot by ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM material_lots WHERE id = ?", (lot_id,)).fetchone()
    conn.close()
    return row


def update_material_lot_status(lot_id, status, released_by=None):
    """Update a material lot's status (Release or Reject)."""
    conn = get_connection()
    try:
        if status in ('Released', 'Rejected') and released_by:
            conn.execute(
                "UPDATE material_lots SET status = ?, released_by = ?, released_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, released_by, lot_id),
            )
        else:
            conn.execute(
                "UPDATE material_lots SET status = ? WHERE id = ?",
                (status, lot_id),
            )
        conn.commit()
    finally:
        conn.close()


# ===========================================================================
# Batches (Production Batch Lifecycle)
# ===========================================================================

def create_batch(batch_number, product_id, created_by, batch_size=None):
    """Create a new production batch in 'Created' status."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO batches (batch_number, product_id, batch_size, created_by)
               VALUES (?, ?, ?, ?)""",
            (batch_number, product_id, batch_size, created_by),
        )
        conn.commit()
    finally:
        conn.close()


def get_batch(batch_id):
    """Return a single batch by ID with product info."""
    conn = get_connection()
    row = conn.execute(
        """SELECT b.*, p.product_name, p.form as product_form,
                  ps.stage_code as current_stage_code, ps.stage_name as current_stage_name
           FROM batches b
           JOIN products p ON b.product_id = p.id
           LEFT JOIN production_stages ps ON b.current_stage_id = ps.id
           WHERE b.id = ?""",
        (batch_id,)
    ).fetchone()
    conn.close()
    return row


def get_batch_by_number(batch_number):
    """Return a single batch by batch number."""
    conn = get_connection()
    row = conn.execute(
        """SELECT b.*, p.product_name, p.form as product_form,
                  ps.stage_code as current_stage_code, ps.stage_name as current_stage_name
           FROM batches b
           JOIN products p ON b.product_id = p.id
           LEFT JOIN production_stages ps ON b.current_stage_id = ps.id
           WHERE b.batch_number = ?""",
        (batch_number,)
    ).fetchone()
    conn.close()
    return row


def get_all_batches(status=None, product_id=None):
    """Return all batches, optionally filtered."""
    conn = get_connection()
    query = """SELECT b.*, p.product_name, p.form as product_form,
                      ps.stage_code as current_stage_code, ps.stage_name as current_stage_name
               FROM batches b
               JOIN products p ON b.product_id = p.id
               LEFT JOIN production_stages ps ON b.current_stage_id = ps.id
               WHERE 1=1"""
    params = []
    if status:
        query += " AND b.status = ?"
        params.append(status)
    if product_id:
        query += " AND b.product_id = ?"
        params.append(product_id)
    query += " ORDER BY b.created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def update_batch_status(batch_id, status, current_stage_id=None,
                        released_by=None):
    """Update batch status and optionally the current stage."""
    conn = get_connection()
    try:
        sets = ["status = ?"]
        params = [status]
        if current_stage_id is not None:
            sets.append("current_stage_id = ?")
            params.append(current_stage_id)
        if status == 'Released' and released_by:
            sets.append("released_by = ?")
            params.append(released_by)
            sets.append("released_at = CURRENT_TIMESTAMP")
        params.append(batch_id)
        conn.execute(
            f"UPDATE batches SET {', '.join(sets)} WHERE id = ?", params
        )
        conn.commit()
    finally:
        conn.close()


# ===========================================================================
# Batch ↔ Material Links
# ===========================================================================

def link_batch_material(batch_id, material_lot_id, quantity_used=None, unit=''):
    """Link a material lot to a production batch."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO batch_materials (batch_id, material_lot_id, quantity_used, unit) VALUES (?, ?, ?, ?)",
            (batch_id, material_lot_id, quantity_used, unit),
        )
        conn.commit()
    finally:
        conn.close()


def get_batch_materials(batch_id):
    """Return material lots linked to a batch."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT bm.*, ml.material_name, ml.lot_number, ml.material_type,
                  ml.supplier, ml.status as lot_status
           FROM batch_materials bm
           JOIN material_lots ml ON bm.material_lot_id = ml.id
           WHERE bm.batch_id = ?""",
        (batch_id,)
    ).fetchall()
    conn.close()
    return rows


# ===========================================================================
# Batch Stage Results (Gate Sign-offs)
# ===========================================================================

def insert_batch_stage_result(batch_id, stage_id, verdict, signed_by=None, notes=''):
    """Insert or update a stage result for a batch (upsert on UNIQUE constraint)."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO batch_stage_results (batch_id, stage_id, verdict, signed_by, signed_at, notes)
               VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
               ON CONFLICT(batch_id, stage_id) DO UPDATE SET
                   verdict = excluded.verdict,
                   signed_by = excluded.signed_by,
                   signed_at = excluded.signed_at,
                   notes = excluded.notes""",
            (batch_id, stage_id, verdict, signed_by, notes),
        )
        conn.commit()
    finally:
        conn.close()


def get_batch_stage_results(batch_id):
    """Return all stage results for a batch, joined with stage info."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT bsr.*, ps.stage_code, ps.stage_name, ps.layer, ps.sequence_order
           FROM batch_stage_results bsr
           JOIN production_stages ps ON bsr.stage_id = ps.id
           WHERE bsr.batch_id = ?
           ORDER BY ps.sequence_order""",
        (batch_id,)
    ).fetchall()
    conn.close()
    return rows


def get_stage_result(batch_id, stage_id):
    """Return a single stage result."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM batch_stage_results WHERE batch_id = ? AND stage_id = ?",
        (batch_id, stage_id)
    ).fetchone()
    conn.close()
    return row


def can_start_stage(batch_id, stage_id):
    """Check whether all prerequisite stages have PASS verdict.

    Prerequisites = all stages with lower sequence_order that share the
    same product_form (or are IQC, which applies to all).
    """
    conn = get_connection()
    try:
        # Get the target stage
        target = conn.execute(
            "SELECT * FROM production_stages WHERE id = ?", (stage_id,)
        ).fetchone()
        if not target:
            return False

        # Get batch's product form
        batch = conn.execute(
            """SELECT p.form FROM batches b JOIN products p ON b.product_id = p.id
               WHERE b.id = ?""", (batch_id,)
        ).fetchone()
        if not batch:
            return False

        # Get all prerequisite stages (lower sequence_order, matching form or IQC)
        prereqs = conn.execute(
            """SELECT ps.id FROM production_stages ps
               WHERE ps.sequence_order < ?
                 AND (ps.product_form = ? OR ps.product_form IS NULL)""",
            (target['sequence_order'], batch['form'])
        ).fetchall()

        if not prereqs:
            return True  # First stage, no prerequisites

        # Check all prereqs have PASS verdict
        prereq_ids = [r['id'] for r in prereqs]
        placeholders = ','.join('?' * len(prereq_ids))
        passed = conn.execute(
            f"""SELECT COUNT(*) as cnt FROM batch_stage_results
                WHERE batch_id = ? AND stage_id IN ({placeholders}) AND verdict = 'PASS'""",
            [batch_id] + prereq_ids
        ).fetchone()

        return passed['cnt'] == len(prereq_ids)
    finally:
        conn.close()


# ===========================================================================
# CAPA — Extended for QC Failures
# ===========================================================================

def insert_capa_from_qc(batch_id, stage_id, root_cause, corrective_action,
                        preventive_action, manager_assigned):
    """Log a CAPA originating from a QC failure (not a customer complaint)."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO capa_logs
               (review_id, root_cause, corrective_action, preventive_action,
                manager_assigned, batch_id, stage_id, source_type)
               VALUES (NULL, ?, ?, ?, ?, ?, ?, 'qc_failure')""",
            (root_cause, corrective_action, preventive_action,
             manager_assigned, batch_id, stage_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_all_capa_logs_extended():
    """Return all CAPA logs with source info (complaint or QC failure)."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT c.*,
               r.batch_number as review_batch, r.product_type, r.review_text, r.ai_category,
               b.batch_number as qc_batch, ps.stage_code, ps.stage_name
        FROM capa_logs c
        LEFT JOIN reviews r ON c.review_id = r.id
        LEFT JOIN batches b ON c.batch_id = b.id
        LEFT JOIN production_stages ps ON c.stage_id = ps.id
        ORDER BY c.resolved_at DESC
    """).fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# Stage Checkpoint Library (Master Spec Library)
# ---------------------------------------------------------------------------

# Fields that operators are allowed to edit on a checkpoint row
EDITABLE_CHECKPOINT_FIELDS = {
    'sample_size', 'sample_count', 'instruction',
    'tolerance', 'unit', 'tol_min', 'tol_max',
    'frequency', 'defect_type', 'test_type', 'result_type',
}


def get_stage_library():
    """Return all stages and their active checkpoints, grouped by layer.

    Structure:
      [
        {
          'layer': 'IQC',
          'stages': [
             {'id':.., 'stage_code':..., 'stage_name':..., 'product_form':...,
              'sequence_order':..., 'checkpoints': [ {...}, ... ]}
          ]
        },
        ...
      ]
    """
    conn = get_connection()
    stages = conn.execute("""
        SELECT * FROM production_stages
        ORDER BY
          CASE layer WHEN 'IQC' THEN 1 WHEN 'IPQC' THEN 2 WHEN 'FQC' THEN 3 ELSE 4 END,
          sequence_order
    """).fetchall()

    checkpoints = conn.execute("""
        SELECT * FROM stage_checkpoints
        WHERE COALESCE(is_active, 1) = 1
        ORDER BY stage_id, id
    """).fetchall()
    conn.close()

    by_stage = {}
    for cp in checkpoints:
        by_stage.setdefault(cp['stage_id'], []).append(dict(cp))

    result = {}
    for s in stages:
        layer = s['layer']
        if layer not in result:
            result[layer] = []
        result[layer].append({
            **dict(s),
            'checkpoints': by_stage.get(s['id'], []),
        })

    # Return as ordered list
    ordered_layers = ['IQC', 'IPQC', 'FQC']
    return [{'layer': l, 'stages': result.get(l, [])} for l in ordered_layers if l in result]


def update_stage_checkpoint_field(checkpoint_id, field, new_value, user, reason=''):
    """Update a single editable field and write an audit entry.

    Returns (True, None) on success, (False, error_message) otherwise.
    """
    if field not in EDITABLE_CHECKPOINT_FIELDS:
        return False, f"Field '{field}' is not editable."

    conn = get_connection()
    try:
        row = conn.execute(
            f"SELECT {field} FROM stage_checkpoints WHERE id = ?", (checkpoint_id,)
        ).fetchone()
        if not row:
            conn.close()
            return False, "Checkpoint not found."

        old_value = row[field]

        # Coerce numeric fields
        coerced = new_value
        if field in ('sample_count',):
            coerced = int(new_value) if str(new_value).strip() else 1
        elif field in ('tol_min', 'tol_max'):
            s = str(new_value).strip()
            coerced = float(s) if s not in ('', 'None', 'null') else None

        conn.execute(
            f"UPDATE stage_checkpoints SET {field} = ?, updated_at = CURRENT_TIMESTAMP, updated_by = ? WHERE id = ?",
            (coerced, user, checkpoint_id)
        )

        # Auto-reparse tolerance text -> numeric bounds when tolerance itself is edited
        if field == 'tolerance':
            lo, hi = parse_tolerance(coerced)
            conn.execute(
                "UPDATE stage_checkpoints SET tol_min = ?, tol_max = ? WHERE id = ?",
                (lo, hi, checkpoint_id)
            )

        conn.execute(
            """INSERT INTO stage_checkpoints_audit
               (checkpoint_id, action, field_changed, old_value, new_value, changed_by, reason)
               VALUES (?, 'EDIT', ?, ?, ?, ?, ?)""",
            (checkpoint_id, field, str(old_value) if old_value is not None else '',
             str(coerced) if coerced is not None else '', user, reason)
        )
        conn.commit()
        conn.close()
        return True, None
    except Exception as e:
        conn.close()
        return False, str(e)


def insert_custom_stage_checkpoint(stage_id, data, user):
    """Create a user-added checkpoint under an existing stage. Returns new id."""
    conn = get_connection()
    tol_min, tol_max = parse_tolerance(data.get('tolerance', ''))
    cur = conn.execute(
        """INSERT INTO stage_checkpoints
           (stage_id, section, checkpoint_no, checkpoint_name, sample_size, sample_count,
            instruction, tolerance, unit, tol_min, tol_max, frequency, defect_type,
            test_type, result_type, source, is_active, updated_at, updated_by)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Custom', 1, CURRENT_TIMESTAMP, ?)""",
        (
            stage_id,
            data.get('section', ''),
            data.get('checkpoint_no', ''),
            data['checkpoint_name'],
            data.get('sample_size', ''),
            int(data.get('sample_count') or 1),
            data.get('instruction', ''),
            data.get('tolerance', ''),
            data.get('unit', ''),
            tol_min, tol_max,
            data.get('frequency', ''),
            data.get('defect_type', ''),
            data.get('test_type', 'variable'),
            data.get('result_type', 'numeric'),
            user,
        )
    )
    new_id = cur.lastrowid
    conn.execute(
        """INSERT INTO stage_checkpoints_audit
           (checkpoint_id, action, field_changed, old_value, new_value, changed_by, reason)
           VALUES (?, 'ADD', NULL, NULL, ?, ?, ?)""",
        (new_id, data['checkpoint_name'], user, data.get('reason', 'Custom addition'))
    )
    conn.commit()
    conn.close()
    return new_id


def deactivate_stage_checkpoint(checkpoint_id, user, reason=''):
    """Soft-delete a checkpoint (custom or inherited).  Returns (ok, msg)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT checkpoint_name, source FROM stage_checkpoints WHERE id = ?", (checkpoint_id,)
    ).fetchone()
    if not row:
        conn.close()
        return False, "Checkpoint not found."
    conn.execute(
        "UPDATE stage_checkpoints SET is_active = 0, updated_at = CURRENT_TIMESTAMP, updated_by = ? WHERE id = ?",
        (user, checkpoint_id)
    )
    conn.execute(
        """INSERT INTO stage_checkpoints_audit
           (checkpoint_id, action, field_changed, old_value, new_value, changed_by, reason)
           VALUES (?, 'DEACTIVATE', NULL, ?, 'inactive', ?, ?)""",
        (checkpoint_id, row['checkpoint_name'], user, reason)
    )
    conn.commit()
    conn.close()
    return True, None


def get_checkpoint_audit_log(checkpoint_id):
    """Return the full audit history for a checkpoint, newest first."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM stage_checkpoints_audit
           WHERE checkpoint_id = ?
           ORDER BY changed_at DESC""",
        (checkpoint_id,)
    ).fetchall()
    conn.close()
    return rows
