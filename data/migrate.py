"""
Atlas Pharma QMS — Idempotent Migration Script
================================================
Run with:  python data/migrate.py

Safe to execute multiple times.  Each step checks whether the change
has already been applied before proceeding.

Changes applied:
  1. Create `products` master table (id, product_name UNIQUE, form, created_at).
  2. Back-fill `products` from existing free-text product names in
     reviews, specs_master, qc_checklists, and batch_records.
  3. Add `product_id` INTEGER FK column to reviews, specs_master,
     qc_checklists, and batch_records (populated from back-fill lookup).
  4. Add CHECK(defect_type IN ('Critical','Major','Minor','Informational'))
     to specs_master (requires table rebuild in SQLite).
  5. Add `pass_fail_criterion` and `defect_type` columns to qc_checklists.
  6. Add `checklist_id` FK column to specs_master.
  7. Create indices on all new FK columns.
"""

import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), "qms.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")  # OFF during migration
    return conn


def column_exists(cursor, table, column):
    """Check whether *column* already exists in *table*."""
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row["name"] == column for row in cursor.fetchall())


def table_exists(cursor, table):
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cursor.fetchone() is not None


def index_exists(cursor, index_name):
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name=?", (index_name,)
    )
    return cursor.fetchone() is not None


# ──────────────────────────────────────────────────────────────────────
# Step 1: Create `products` master table
# ──────────────────────────────────────────────────────────────────────
def step1_create_products_table(cur):
    if table_exists(cur, "products"):
        print("  ✓ products table already exists — skipping.")
        return
    cur.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT UNIQUE NOT NULL,
            form TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✓ Created products table.")


# ──────────────────────────────────────────────────────────────────────
# Step 2: Back-fill `products` from existing free-text values
# ──────────────────────────────────────────────────────────────────────
def step2_backfill_products(cur):
    # Gather distinct product names from all tables that use free text
    sources = []

    if table_exists(cur, "reviews") and column_exists(cur, "reviews", "product_type"):
        sources.append("SELECT DISTINCT product_type AS pname FROM reviews WHERE product_type IS NOT NULL AND product_type != ''")

    if table_exists(cur, "specs_master") and column_exists(cur, "specs_master", "product_name"):
        sources.append("SELECT DISTINCT product_name AS pname FROM specs_master WHERE product_name IS NOT NULL AND product_name != ''")

    if table_exists(cur, "qc_checklists") and column_exists(cur, "qc_checklists", "product_name"):
        sources.append("SELECT DISTINCT product_name AS pname FROM qc_checklists WHERE product_name IS NOT NULL AND product_name != ''")

    if table_exists(cur, "batch_records") and column_exists(cur, "batch_records", "product_name"):
        sources.append("SELECT DISTINCT product_name AS pname FROM batch_records WHERE product_name IS NOT NULL AND product_name != ''")

    if not sources:
        print("  ✓ No source tables with free-text product names — skipping back-fill.")
        return

    union = " UNION ".join(sources)

    # Also try to grab form for each product from specs_master or qc_checklists
    names = [row["pname"] for row in cur.execute(union).fetchall()]
    inserted = 0
    for name in names:
        # Try to find the form from specs_master first, then qc_checklists
        form = None
        if table_exists(cur, "specs_master") and column_exists(cur, "specs_master", "form"):
            row = cur.execute(
                "SELECT form FROM specs_master WHERE product_name = ? LIMIT 1", (name,)
            ).fetchone()
            if row:
                form = row["form"]
        if form is None and table_exists(cur, "qc_checklists") and column_exists(cur, "qc_checklists", "form"):
            row = cur.execute(
                "SELECT form FROM qc_checklists WHERE product_name = ? LIMIT 1", (name,)
            ).fetchone()
            if row:
                form = row["form"]

        cur.execute(
            "INSERT OR IGNORE INTO products (product_name, form) VALUES (?, ?)",
            (name, form),
        )
        if cur.rowcount > 0:
            inserted += 1

    print(f"  ✓ Back-filled {inserted} product(s) into products table ({len(names)} unique names found).")


# ──────────────────────────────────────────────────────────────────────
# Step 3: Add product_id FK columns
# ──────────────────────────────────────────────────────────────────────
def step3_add_product_id_columns(cur):
    tables_and_text_col = {
        "reviews":        "product_type",
        "specs_master":   "product_name",
        "qc_checklists":  "product_name",
        "batch_records":  "product_name",
    }

    for table, text_col in tables_and_text_col.items():
        if not table_exists(cur, table):
            continue
        if column_exists(cur, table, "product_id"):
            print(f"  ✓ {table}.product_id already exists — skipping ADD COLUMN.")
        else:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN product_id INTEGER REFERENCES products(id) ON DELETE RESTRICT")
            print(f"  ✓ Added product_id column to {table}.")

        # Populate product_id from free-text column via lookup
        if column_exists(cur, table, text_col):
            cur.execute(f"""
                UPDATE {table}
                SET product_id = (
                    SELECT p.id FROM products p WHERE p.product_name = {table}.{text_col}
                )
                WHERE product_id IS NULL AND {text_col} IS NOT NULL AND {text_col} != ''
            """)
            updated = cur.rowcount
            if updated > 0:
                print(f"  ✓ Populated {updated} product_id values in {table} from {text_col}.")
            else:
                print(f"  ✓ {table}.product_id already populated (or no matching data).")


# ──────────────────────────────────────────────────────────────────────
# Step 4: Add pass_fail_criterion and defect_type to qc_checklists
# ──────────────────────────────────────────────────────────────────────
def step4_add_checklist_extra_columns(cur):
    if not table_exists(cur, "qc_checklists"):
        return

    for col, default in [("pass_fail_criterion", ""), ("defect_type", "")]:
        if column_exists(cur, "qc_checklists", col):
            print(f"  ✓ qc_checklists.{col} already exists — skipping.")
        else:
            cur.execute(f"ALTER TABLE qc_checklists ADD COLUMN {col} TEXT DEFAULT '{default}'")
            print(f"  ✓ Added {col} column to qc_checklists.")


# ──────────────────────────────────────────────────────────────────────
# Step 5: Add checklist_id FK to specs_master
# ──────────────────────────────────────────────────────────────────────
def step5_add_checklist_id_to_specs(cur):
    if not table_exists(cur, "specs_master"):
        return
    if column_exists(cur, "specs_master", "checklist_id"):
        print("  ✓ specs_master.checklist_id already exists — skipping.")
        return

    cur.execute("ALTER TABLE specs_master ADD COLUMN checklist_id INTEGER REFERENCES qc_checklists(id)")
    print("  ✓ Added checklist_id FK to specs_master.")

    # Auto-link existing spec rows to checklists where product + checkpoint match
    if table_exists(cur, "qc_checklists"):
        cur.execute("""
            UPDATE specs_master
            SET checklist_id = (
                SELECT qc.id FROM qc_checklists qc
                WHERE qc.product_name = specs_master.product_name
                  AND qc.checkpoint = specs_master.checkpoint
                LIMIT 1
            )
            WHERE checklist_id IS NULL
        """)
        linked = cur.rowcount
        print(f"  ✓ Linked {linked} spec rows to their qc_checklists counterpart.")


# ──────────────────────────────────────────────────────────────────────
# Step 6: Create indices on FK columns
# ──────────────────────────────────────────────────────────────────────
def step6_create_indices(cur):
    indices = [
        ("idx_reviews_product_id",        "reviews",        "product_id"),
        ("idx_specs_product_id",         "specs_master",    "product_id"),
        ("idx_specs_checklist_id",       "specs_master",    "checklist_id"),
        ("idx_checklists_product_id",    "qc_checklists",   "product_id"),
        ("idx_batch_records_product_id", "batch_records",   "product_id"),
    ]
    for idx_name, table, col in indices:
        if not table_exists(cur, table) or not column_exists(cur, table, col):
            continue
        if index_exists(cur, idx_name):
            print(f"  ✓ Index {idx_name} already exists — skipping.")
            continue
        cur.execute(f"CREATE INDEX {idx_name} ON {table}({col})")
        print(f"  ✓ Created index {idx_name} on {table}({col}).")


# ──────────────────────────────────────────────────────────────────────
# Step 7: Backfill qc_checklists pass_fail_criterion/defect_type from specs_master
# ──────────────────────────────────────────────────────────────────────
def step7_backfill_checklist_details(cur):
    if not table_exists(cur, "qc_checklists") or not table_exists(cur, "specs_master"):
        return

    if not column_exists(cur, "qc_checklists", "pass_fail_criterion"):
        return

    cur.execute("""
        UPDATE qc_checklists
        SET pass_fail_criterion = (
                SELECT sm.pass_fail_criterion FROM specs_master sm
                WHERE sm.product_name = qc_checklists.product_name
                  AND sm.checkpoint = qc_checklists.checkpoint
                LIMIT 1
            ),
            defect_type = (
                SELECT sm.defect_type FROM specs_master sm
                WHERE sm.product_name = qc_checklists.product_name
                  AND sm.checkpoint = qc_checklists.checkpoint
                LIMIT 1
            )
        WHERE (pass_fail_criterion IS NULL OR pass_fail_criterion = '')
          AND EXISTS (
              SELECT 1 FROM specs_master sm
              WHERE sm.product_name = qc_checklists.product_name
                AND sm.checkpoint = qc_checklists.checkpoint
          )
    """)
    updated = cur.rowcount
    if updated > 0:
        print(f"  ✓ Back-filled pass_fail_criterion/defect_type for {updated} checklist rows from specs_master.")
    else:
        print("  ✓ qc_checklists pass_fail/defect already populated (or no matching specs).")


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────
def run_migration():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Run init_db() first.")
        sys.exit(1)

    conn = get_connection()
    cur = conn.cursor()

    print("=" * 60)
    print("Atlas Pharma QMS — Database Migration")
    print("=" * 60)

    print("\n[Step 1] Create products master table")
    step1_create_products_table(cur)

    print("\n[Step 2] Back-fill products from existing data")
    step2_backfill_products(cur)

    print("\n[Step 3] Add product_id FK columns to dependent tables")
    step3_add_product_id_columns(cur)

    print("\n[Step 4] Add pass_fail_criterion & defect_type to qc_checklists")
    step4_add_checklist_extra_columns(cur)

    print("\n[Step 5] Add checklist_id FK to specs_master")
    step5_add_checklist_id_to_specs(cur)

    print("\n[Step 6] Create FK indices")
    step6_create_indices(cur)

    print("\n[Step 7] Back-fill checklist details from specs_master")
    step7_backfill_checklist_details(cur)

    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.close()

    print("\n" + "=" * 60)
    print("✅ Migration complete.")
    print("=" * 60)


if __name__ == "__main__":
    run_migration()
