"""
Atlas Pharma QMS — Seed Data
Pre-populates the database with default users, products, specs, and lab partners.
Run once after DB initialization.
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from db_manager import create_user, get_connection, get_or_create_product


def seed_users():
    """Create default user accounts."""
    create_user("admin", "atlas2026", "Admin User", "Admin")
    create_user("maimouna", "atlas2026", "Maimouna Diabi", "Quality Manager")
    create_user("busra", "atlas2026", "Büşra", "Quality Manager")
    create_user("executive", "atlas2026", "Executive Viewer", "Executive")


def seed_products():
    """Ensure master product records exist."""
    get_or_create_product("Paracetamol Tablet 500 mg", "Tablet")
    get_or_create_product("Paracetamol Syrup 120 mg/5 mL", "Syrup")


def seed_specs():
    """Insert Paracetamol Tablet and Syrup QC checklist specifications."""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) as c FROM specs_master").fetchone()["c"]
    if count > 0:
        conn.close()
        return

    # Look up product IDs
    tablet = conn.execute("SELECT id FROM products WHERE product_name = ?",
                          ("Paracetamol Tablet 500 mg",)).fetchone()
    syrup = conn.execute("SELECT id FROM products WHERE product_name = ?",
                         ("Paracetamol Syrup 120 mg/5 mL",)).fetchone()
    tablet_id = tablet["id"] if tablet else None
    syrup_id = syrup["id"] if syrup else None

    specs = [
        # (product_name, product_id, form, checkpoint, sample_size, test_method, tolerance, pass_fail_criterion, defect_type)
        # Paracetamol Tablet 500 mg
        ("Paracetamol Tablet 500 mg", tablet_id, "Tablet", "Appearance",
         "100%", "Visual inspection", "White to off-white, round, biconvex",
         "Pass if conforms", "Critical"),
        ("Paracetamol Tablet 500 mg", tablet_id, "Tablet", "Average Weight",
         "10 tablets / batch", "USP <791> Weight Variation", "550 ± 5% mg",
         "Pass if within ±5%", "Major"),
        ("Paracetamol Tablet 500 mg", tablet_id, "Tablet", "Hardness",
         "6 tablets / batch", "Tablet hardness tester", "5 – 10 kp",
         "Pass if 5-10 kp", "Minor"),
        ("Paracetamol Tablet 500 mg", tablet_id, "Tablet", "Friability",
         "1 sample / batch", "USP <1216> Friability", "≤ 1.0%",
         "Pass if ≤ 1.0%", "Major"),
        ("Paracetamol Tablet 500 mg", tablet_id, "Tablet", "Disintegration Time",
         "6 tablets / batch", "USP <701> Disintegration", "≤ 15 minutes",
         "Pass if ≤ 15 min", "Critical"),
        ("Paracetamol Tablet 500 mg", tablet_id, "Tablet", "Assay (Paracetamol)",
         "Composite sample", "HPLC (USP Monograph)", "95.0 – 105.0% of label claim",
         "Pass if 95-105%", "Critical"),
        ("Paracetamol Tablet 500 mg", tablet_id, "Tablet", "Dissolution",
         "6 tablets / batch", "USP <711> Dissolution Apparatus II", "≥ 80% in 30 min",
         "Pass if ≥ 80%", "Critical"),
        ("Paracetamol Tablet 500 mg", tablet_id, "Tablet", "Moisture Content",
         "1 sample / batch", "Karl Fischer titration", "≤ 3.0%",
         "Pass if ≤ 3.0%", "Major"),
        ("Paracetamol Tablet 500 mg", tablet_id, "Tablet", "Microbial Limits",
         "Composite sample", "USP <61>/<62>", "TAMC ≤ 10³ CFU/g, TYMC ≤ 10² CFU/g",
         "Pass if within limits", "Critical"),
        # Paracetamol Syrup 120 mg/5 mL
        ("Paracetamol Syrup 120 mg/5 mL", syrup_id, "Syrup", "Appearance",
         "100%", "Visual / Organoleptic", "Clear, colorless to pale-yellow, cherry-flavored",
         "Pass if conforms", "Critical"),
        ("Paracetamol Syrup 120 mg/5 mL", syrup_id, "Syrup", "pH",
         "3 bottles / batch", "pH meter (USP <791>)", "4.5 – 6.5",
         "Pass if 4.5-6.5", "Major"),
        ("Paracetamol Syrup 120 mg/5 mL", syrup_id, "Syrup", "Specific Gravity",
         "3 bottles / batch", "Densitometer", "1.10 – 1.25 g/mL",
         "Pass if 1.10-1.25", "Minor"),
        ("Paracetamol Syrup 120 mg/5 mL", syrup_id, "Syrup", "Assay (Paracetamol)",
         "Composite sample", "HPLC (USP Monograph)", "90.0 – 110.0% of label claim",
         "Pass if 90-110%", "Critical"),
        ("Paracetamol Syrup 120 mg/5 mL", syrup_id, "Syrup", "Volume per Container",
         "5 bottles / batch", "Graduated cylinder", "100 mL ± 2%",
         "Pass if 98-102 mL", "Major"),
        ("Paracetamol Syrup 120 mg/5 mL", syrup_id, "Syrup", "Preservative Content",
         "Composite sample", "HPLC", "Within approved limits",
         "Pass if within limits", "Major"),
        ("Paracetamol Syrup 120 mg/5 mL", syrup_id, "Syrup", "Microbial Limits",
         "Composite sample", "USP <61>/<62>", "TAMC ≤ 10² CFU/mL, TYMC ≤ 10¹ CFU/mL, No E. coli",
         "Pass if within limits", "Critical"),
        ("Paracetamol Syrup 120 mg/5 mL", syrup_id, "Syrup", "Viscosity",
         "3 bottles / batch", "Brookfield viscometer", "50 – 200 cP",
         "Pass if 50-200 cP", "Minor"),
    ]

    conn.executemany(
        """INSERT INTO specs_master 
           (product_name, product_id, form, checkpoint, sample_size, test_method, tolerance, pass_fail_criterion, defect_type)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        specs,
    )
    conn.commit()
    conn.close()


def seed_partners():
    """Insert Turkish testing institutions and regulatory bodies."""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) as c FROM partners_directory").fetchone()["c"]
    if count > 0:
        conn.close()
        return

    partners = [
        ("TSE (Türk Standartları Enstitüsü)", "Standards Body", "TS EN ISO 9001, TS EN ISO 13485",
         "Necatibey Cad. No:112, Bakanlıklar, Ankara | +90 312 416 60 00",
         "National standards body. Certifies GMP and quality management systems for pharmaceutical manufacturing."),
        ("TÜBİTAK MAM", "Research Laboratory", "ISO/IEC 17025, GLP Compliance",
         "Gebze Yerleşkesi, 41470 Kocaeli | +90 262 677 30 00",
         "Government research lab. Performs advanced analytical testing (HPLC, dissolution, stability studies) for pharma."),
        ("TİTCK (Türkiye İlaç ve Tıbbi Cihaz Kurumu)", "Regulatory Authority", "ICH Guidelines, GMP, GDP",
         "Söğütözü Mah. 2176. Sok. No:5, Çankaya, Ankara | +90 312 218 30 00",
         "Turkish Medicines Agency. Grants marketing authorization, conducts GMP inspections, and monitors pharmacovigilance."),
        ("SGS Türkiye", "Third-Party Testing", "ISO 17025, FDA 21 CFR Part 11",
         "Maltepe, İstanbul | +90 216 368 04 00",
         "International inspection & certification. Performs raw material testing, finished product analysis, and audits."),
        ("Intertek Türkiye", "Third-Party Testing", "ISO 17025, ISTA Standards",
         "Kavacık, Beykoz, İstanbul | +90 216 680 00 90",
         "Packaging integrity testing (ISTA), transport simulation, and stability chamber testing for pharma logistics."),
    ]

    conn.executemany(
        "INSERT INTO partners_directory (institution_name, type, standards, contact_info, notes) VALUES (?, ?, ?, ?, ?)",
        partners,
    )
    conn.commit()
    conn.close()


def seed_sample_reviews():
    """Insert a handful of sample reviews for demo purposes."""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) as c FROM reviews").fetchone()["c"]
    if count > 0:
        conn.close()
        return

    # Look up product IDs
    tablet = conn.execute("SELECT id FROM products WHERE product_name = ?",
                          ("Paracetamol Tablet 500 mg",)).fetchone()
    syrup = conn.execute("SELECT id FROM products WHERE product_name = ?",
                         ("Paracetamol Syrup 120 mg/5 mL",)).fetchone()
    tablet_id = tablet["id"] if tablet else None
    syrup_id = syrup["id"] if syrup else None

    reviews = [
        ("BTX-2026-0417", "Paracetamol Tablet 500 mg", tablet_id,
         "Found discoloration on tablets from this batch. Some pills have yellowish spots on the surface.",
         "Major", "Negative", "Open"),
        ("BSY-2026-0312", "Paracetamol Syrup 120 mg/5 mL", syrup_id,
         "The syrup has an unusual bitter aftertaste that is different from previous batches.",
         "Minor", "Negative", "Open"),
        ("BTX-2026-0390", "Paracetamol Tablet 500 mg", tablet_id,
         "Several tablets in the blister pack were crumbled/broken upon opening. Packaging integrity issue.",
         "Critical", "Negative", "Open"),
        ("BSY-2026-0288", "Paracetamol Syrup 120 mg/5 mL", syrup_id,
         "Product consistency seems thinner than usual. Pours faster than the older batch we had.",
         "Minor", "Negative", "Claimed"),
        ("BTX-2026-0401", "Paracetamol Tablet 500 mg", tablet_id,
         "Excellent batch quality. Tablets are well-formed and dissolve properly in water tests.",
         "Minor", "Positive", "Resolved"),
    ]

    for r in reviews:
        conn.execute(
            """INSERT INTO reviews (batch_number, product_type, product_id, review_text, ai_category, ai_sentiment, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            r,
        )
    conn.commit()
    conn.close()


def seed_qc_checklists():
    """Insert QC checklist definitions for Tablet and Syrup products."""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) as c FROM qc_checklists").fetchone()["c"]
    if count > 0:
        conn.close()
        return

    # Look up product IDs
    tablet = conn.execute("SELECT id FROM products WHERE product_name = ?",
                          ("Paracetamol Tablet 500 mg",)).fetchone()
    syrup = conn.execute("SELECT id FROM products WHERE product_name = ?",
                         ("Paracetamol Syrup 120 mg/5 mL",)).fetchone()
    tablet_id = tablet["id"] if tablet else None
    syrup_id = syrup["id"] if syrup else None

    checklists = [
        # (product_name, product_id, form, checkpoint, sample_size, sample_count,
        #  tolerance, unit, tol_min, tol_max, test_type, test_method,
        #  pass_fail_criterion, defect_type)

        # Paracetamol Tablet 500 mg
        ("Paracetamol Tablet 500 mg", tablet_id, "Tablet", "Weight Variation",
         "10 tablets / batch", 10, "550 ± 5% mg", "mg", 522.5, 577.5,
         "variable", "USP <791> Weight Variation", "Pass if within ±5%", "Major"),
        ("Paracetamol Tablet 500 mg", tablet_id, "Tablet", "Hardness",
         "6 tablets / batch", 6, "5 – 10 kp", "kp", 5.0, 10.0,
         "variable", "Tablet hardness tester", "Pass if 5-10 kp", "Minor"),
        ("Paracetamol Tablet 500 mg", tablet_id, "Tablet", "Disintegration Time",
         "6 tablets / batch", 6, "≤ 15 min", "min", 0.0, 15.0,
         "variable", "USP <701> Disintegration", "Pass if ≤ 15 min", "Critical"),
        ("Paracetamol Tablet 500 mg", tablet_id, "Tablet", "Friability",
         "1 sample / batch", 1, "≤ 1.0 %", "%", 0.0, 1.0,
         "variable", "USP <1216> Friability", "Pass if ≤ 1.0%", "Major"),

        # Paracetamol Syrup 120 mg/5 mL
        ("Paracetamol Syrup 120 mg/5 mL", syrup_id, "Syrup", "pH",
         "3 bottles / batch", 3, "4.5 – 6.5", "pH", 4.5, 6.5,
         "variable", "pH meter (USP <791>)", "Pass if 4.5-6.5", "Major"),
        ("Paracetamol Syrup 120 mg/5 mL", syrup_id, "Syrup", "Viscosity",
         "3 bottles / batch", 3, "50 – 200 cP", "cP", 50.0, 200.0,
         "variable", "Brookfield viscometer", "Pass if 50-200 cP", "Minor"),
        ("Paracetamol Syrup 120 mg/5 mL", syrup_id, "Syrup", "Specific Gravity",
         "3 bottles / batch", 3, "1.10 – 1.25 g/mL", "g/mL", 1.10, 1.25,
         "variable", "Densitometer", "Pass if 1.10-1.25", "Minor"),
        ("Paracetamol Syrup 120 mg/5 mL", syrup_id, "Syrup", "Volume per Container",
         "5 bottles / batch", 5, "98 – 102 mL", "mL", 98.0, 102.0,
         "variable", "Graduated cylinder", "Pass if 98-102 mL", "Major"),
    ]

    conn.executemany(
        """INSERT INTO qc_checklists
           (product_name, product_id, form, checkpoint, sample_size, sample_count, tolerance,
            unit, tol_min, tol_max, test_type, test_method, pass_fail_criterion, defect_type)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        checklists,
    )
    conn.commit()
    conn.close()


def seed_sample_batch_records():
    """Insert historical batch QC records for SPC demo data."""
    import json
    import random
    random.seed(42)

    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) as c FROM batch_records").fetchone()["c"]
    if count > 0:
        conn.close()
        return

    # Get checklist IDs
    checklists = conn.execute("SELECT * FROM qc_checklists").fetchall()
    if not checklists:
        conn.close()
        return

    cl_map = {}
    for cl in checklists:
        key = (cl['product_name'], cl['checkpoint'])
        cl_map[key] = cl

    # Look up product IDs
    tablet = conn.execute("SELECT id FROM products WHERE product_name = ?",
                          ("Paracetamol Tablet 500 mg",)).fetchone()
    syrup = conn.execute("SELECT id FROM products WHERE product_name = ?",
                         ("Paracetamol Syrup 120 mg/5 mL",)).fetchone()
    tablet_id = tablet["id"] if tablet else None
    syrup_id = syrup["id"] if syrup else None

    # Historical batches for tablets
    tablet_batches = [
        ("BTX-2026-0401", "2026-03-01 09:00:00"),
        ("BTX-2026-0402", "2026-03-05 10:00:00"),
        ("BTX-2026-0403", "2026-03-10 09:30:00"),
        ("BTX-2026-0404", "2026-03-15 11:00:00"),
        ("BTX-2026-0405", "2026-03-20 08:45:00"),
        ("BTX-2026-0406", "2026-03-25 10:15:00"),
        ("BTX-2026-0417", "2026-04-01 09:00:00"),
    ]

    # Historical batches for syrup
    syrup_batches = [
        ("BSY-2026-0288", "2026-03-02 09:00:00"),
        ("BSY-2026-0289", "2026-03-08 10:00:00"),
        ("BSY-2026-0290", "2026-03-14 09:30:00"),
        ("BSY-2026-0291", "2026-03-19 11:00:00"),
        ("BSY-2026-0292", "2026-03-24 08:45:00"),
        ("BSY-2026-0312", "2026-04-02 10:15:00"),
    ]

    records = []

    # Generate tablet QC data
    for batch, ts in tablet_batches:
        # Weight Variation: target ~550, within 522.5-577.5
        cl = cl_map[("Paracetamol Tablet 500 mg", "Weight Variation")]
        vals = [round(random.gauss(550, 8), 1) for _ in range(10)]
        mean_v = round(sum(vals) / len(vals), 2)
        range_v = round(max(vals) - min(vals), 2)
        status = "PASS" if cl['tol_min'] <= mean_v <= cl['tol_max'] else "FAIL"
        records.append((batch, "Paracetamol Tablet 500 mg", tablet_id, cl['id'], "Weight Variation",
                        json.dumps(vals), 10, mean_v, range_v, cl['tol_min'], cl['tol_max'],
                        status, "Maimouna Diabi", ts))

        # Hardness: target ~7.5, within 5-10
        cl = cl_map[("Paracetamol Tablet 500 mg", "Hardness")]
        vals = [round(random.gauss(7.5, 1.0), 1) for _ in range(6)]
        mean_v = round(sum(vals) / len(vals), 2)
        range_v = round(max(vals) - min(vals), 2)
        status = "PASS" if cl['tol_min'] <= mean_v <= cl['tol_max'] else "FAIL"
        records.append((batch, "Paracetamol Tablet 500 mg", tablet_id, cl['id'], "Hardness",
                        json.dumps(vals), 6, mean_v, range_v, cl['tol_min'], cl['tol_max'],
                        status, "Maimouna Diabi", ts))

        # Disintegration: target ~10, within 0-15
        cl = cl_map[("Paracetamol Tablet 500 mg", "Disintegration Time")]
        vals = [round(random.gauss(10, 1.5), 1) for _ in range(6)]
        mean_v = round(sum(vals) / len(vals), 2)
        range_v = round(max(vals) - min(vals), 2)
        status = "PASS" if cl['tol_min'] <= mean_v <= cl['tol_max'] else "FAIL"
        records.append((batch, "Paracetamol Tablet 500 mg", tablet_id, cl['id'], "Disintegration Time",
                        json.dumps(vals), 6, mean_v, range_v, cl['tol_min'], cl['tol_max'],
                        status, "Maimouna Diabi", ts))

    # Generate syrup QC data
    for batch, ts in syrup_batches:
        # pH: target ~5.5, within 4.5-6.5
        cl = cl_map[("Paracetamol Syrup 120 mg/5 mL", "pH")]
        vals = [round(random.gauss(5.5, 0.3), 2) for _ in range(3)]
        mean_v = round(sum(vals) / len(vals), 2)
        range_v = round(max(vals) - min(vals), 2)
        status = "PASS" if cl['tol_min'] <= mean_v <= cl['tol_max'] else "FAIL"
        records.append((batch, "Paracetamol Syrup 120 mg/5 mL", syrup_id, cl['id'], "pH",
                        json.dumps(vals), 3, mean_v, range_v, cl['tol_min'], cl['tol_max'],
                        status, "Büşra", ts))

        # Viscosity: target ~125, within 50-200
        cl = cl_map[("Paracetamol Syrup 120 mg/5 mL", "Viscosity")]
        vals = [round(random.gauss(125, 15), 1) for _ in range(3)]
        mean_v = round(sum(vals) / len(vals), 2)
        range_v = round(max(vals) - min(vals), 2)
        status = "PASS" if cl['tol_min'] <= mean_v <= cl['tol_max'] else "FAIL"
        records.append((batch, "Paracetamol Syrup 120 mg/5 mL", syrup_id, cl['id'], "Viscosity",
                        json.dumps(vals), 3, mean_v, range_v, cl['tol_min'], cl['tol_max'],
                        status, "Büşra", ts))

        # Volume per Container: target ~100, within 98-102
        cl = cl_map[("Paracetamol Syrup 120 mg/5 mL", "Volume per Container")]
        vals = [round(random.gauss(100, 0.6), 1) for _ in range(5)]
        mean_v = round(sum(vals) / len(vals), 2)
        range_v = round(max(vals) - min(vals), 2)
        status = "PASS" if cl['tol_min'] <= mean_v <= cl['tol_max'] else "FAIL"
        records.append((batch, "Paracetamol Syrup 120 mg/5 mL", syrup_id, cl['id'], "Volume per Container",
                        json.dumps(vals), 5, mean_v, range_v, cl['tol_min'], cl['tol_max'],
                        status, "Büşra", ts))

    conn.executemany(
        """INSERT INTO batch_records
           (batch_number, product_name, product_id, checklist_id, checkpoint,
            individual_values, sample_count, mean, range_val,
            tol_min, tol_max, status, tested_by, tested_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        records,
    )
    conn.commit()
    conn.close()


def run_all_seeds():
    """Execute all seed functions."""
    seed_users()
    seed_products()      # Must run before specs, checklists, reviews, batch_records
    seed_specs()
    seed_partners()
    seed_sample_reviews()
    seed_qc_checklists()
    seed_sample_batch_records()


if __name__ == "__main__":
    from db_manager import init_db
    init_db()
    run_all_seeds()
    print("✅ Database seeded successfully.")
