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


def seed_production_stages():
    """Insert the 11 manufacturing stages across IQC, IPQC, and FQC layers."""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) as c FROM production_stages").fetchone()["c"]
    if count > 0:
        conn.close()
        return

    import json

    stages = [
        # (stage_code, stage_name, layer, product_form, sequence_order, equipment_json)
        # ── IQC (shared across both products) ──
        ("RM-001", "API Incoming QC", "IQC", None, 1, json.dumps([
            {"id": "A1", "name": "Visual / Daylight lamp"},
            {"id": "A2", "name": "Fume hood"},
            {"id": "A3", "name": "No equipment"},
            {"id": "A4", "name": "Moisture balance / Drying oven"},
            {"id": "A5", "name": "250 um sieve + shaker"},
            {"id": "A6", "name": "250 mL graduated cylinder + balance"},
            {"id": "A7", "name": "Quarantine labels"},
            {"id": "A8", "name": "PO / CoA / Approved Supplier List"},
        ])),
        ("RM-002", "Excipients Incoming QC", "IQC", None, 2, json.dumps([
            {"id": "E1", "name": "White LED lightbox"},
            {"id": "E2", "name": "Drying oven 105C + analytical balance"},
            {"id": "E3", "name": "Drying oven 105C + analytical balance"},
            {"id": "E4", "name": "White paper (organoleptic)"},
            {"id": "E5", "name": "White lightbox"},
            {"id": "E6", "name": "Inline conductivity meter"},
            {"id": "E7", "name": "Fume hood"},
            {"id": "E8", "name": "Quarantine labels"},
        ])),
        ("PM-001", "Packaging Materials Incoming QC", "IQC", None, 3, json.dumps([
            {"id": "P1", "name": "Approved artwork master + magnifier"},
            {"id": "P2", "name": "Handheld barcode scanner"},
            {"id": "P3", "name": "Digital micrometer"},
            {"id": "P4", "name": "Vernier caliper 150mm"},
            {"id": "P5", "name": "Spring balance / peel tester"},
            {"id": "P6", "name": "Light table"},
            {"id": "P7", "name": "Graduated cylinder 100mL + balance"},
            {"id": "P8", "name": "Digital micrometer"},
            {"id": "P9", "name": "Torque gauge 0-50 Ncm"},
        ])),

        # ── IPQC Tablet ──
        ("IPQC-T-01", "Granulation", "IPQC", "Tablet", 4, json.dumps([
            {"id": "FBD-01", "name": "Fluid Bed Dryer / Oven"},
            {"id": "MA-HALB-01", "name": "Moisture Analyser (Halogen)"},
            {"id": "GRAN-01", "name": "Sieve / Oscillating Granulator"},
            {"id": "BAL-001", "name": "Analytical Balance"},
            {"id": "TEMP-01", "name": "Thermometer / Thermocouple"},
            {"id": "TAP-01", "name": "Bulk / Tap Density Tester"},
        ])),
        ("IPQC-T-02", "Compression", "IPQC", "Tablet", 5, json.dumps([
            {"id": "HARD-01", "name": "Tablet Hardness Tester"},
            {"id": "THICK-01", "name": "Tablet Thickness Gauge"},
            {"id": "CAL-01", "name": "Vernier Caliper"},
            {"id": "BAL-001", "name": "Analytical Balance (0.1 mg)"},
            {"id": "FRIA-01", "name": "Friability Tester (Roche)"},
            {"id": "DISINT-01", "name": "Disintegration Tester"},
            {"id": "MIC-01", "name": "Thickness Micrometer"},
            {"id": "VIS-01", "name": "Stroboscope / Camera"},
        ])),
        ("IPQC-T-03", "Coating & Blistering", "IPQC", "Tablet", 6, json.dumps([
            {"id": "BAL-001", "name": "Analytical Balance"},
            {"id": "TEMP-02", "name": "Coating Pan Thermometers"},
            {"id": "SEAL-01", "name": "Leak / Seal Tester"},
            {"id": "PEEL-01", "name": "Peel Force Tester"},
            {"id": "THICK-01", "name": "Thickness Gauge"},
            {"id": "TORQ-01", "name": "Torque Meter"},
            {"id": "CAL-01", "name": "Vernier Caliper"},
        ])),

        # ── IPQC Syrup ──
        ("IPQC-S-01", "Mixing & Dissolution", "IPQC", "Syrup", 4, json.dumps([
            {"id": "STR-01", "name": "Overhead / Anchor Stirrer"},
            {"id": "BAL-001", "name": "Analytical Balance (0.01 g)"},
            {"id": "PH-01", "name": "Calibrated pH Meter"},
            {"id": "TEMP-S1", "name": "Thermometer / Temp probe"},
            {"id": "REFR-01", "name": "Refractometer (Brix)"},
            {"id": "VIS-01", "name": "Visual inspection light box"},
            {"id": "PW-PANEL", "name": "Purified Water System"},
        ])),
        ("IPQC-S-02", "Physical-Chemical QC", "IPQC", "Syrup", 5, json.dumps([
            {"id": "PH-01", "name": "Calibrated pH Meter"},
            {"id": "VISC-01", "name": "Brookfield LV Viscometer"},
            {"id": "DENS-01", "name": "Specific gravity pycnometer"},
            {"id": "SPEC-01", "name": "Colour comparator / spectrophotometer"},
            {"id": "TURB-01", "name": "Turbidity meter (Nephelometer)"},
            {"id": "HPLC-01", "name": "HPLC System"},
            {"id": "TEMP-S2", "name": "Thermometer"},
        ])),
        ("IPQC-S-03", "Filling & Capping", "IPQC", "Syrup", 6, json.dumps([
            {"id": "FILL-01", "name": "Volumetric Filling Machine"},
            {"id": "BAL-001", "name": "Analytical Balance (0.01 g)"},
            {"id": "GRAD-01", "name": "Graduated cylinder 100/150 mL"},
            {"id": "TORQ-01", "name": "Cap Torque Meter"},
            {"id": "SEAL-01", "name": "Leak / Seal Tester"},
            {"id": "LAB-01", "name": "Label Application Verifier"},
            {"id": "SCAN-01", "name": "Barcode Scanner"},
            {"id": "TEMP-S3", "name": "Thermometer"},
        ])),

        # ── FQC ──
        ("FP-TAB-500", "Finished Product Release - Tablet", "FQC", "Tablet", 7, "[]"),
        ("FP-SYP-125", "Finished Product Release - Syrup", "FQC", "Syrup", 7, "[]"),
    ]

    conn.executemany(
        """INSERT INTO production_stages
           (stage_code, stage_name, layer, product_form, sequence_order, equipment_json)
           VALUES (?, ?, ?, ?, ?, ?)""",
        stages,
    )
    conn.commit()
    conn.close()


def seed_stage_checkpoints():
    """Insert all 208 QC checkpoints across all manufacturing stages."""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) as c FROM stage_checkpoints").fetchone()["c"]
    if count > 0:
        conn.close()
        return

    # Build stage_code -> id map
    stages = conn.execute("SELECT id, stage_code FROM production_stages").fetchall()
    sid = {s['stage_code']: s['id'] for s in stages}

    # Format: (section, no, name, sample_size, sample_count, instruction, tolerance, frequency)
    # We'll insert with stage_id resolved from the dict

    checkpoints = {}

    # ── RM-001: API Incoming QC (21 checks) ──
    checkpoints['RM-001'] = [
        ("A. Identification & Documentation", "1", "Supplier CoA present", "AQL Level II, 1.0", 1,
         "Confirm CoA accompanies each batch; check batch no., mfg date, expiry", "Batch no. = PO no.", "Per receipt"),
        ("A. Identification & Documentation", "2", "Label verification (material name, grade, batch no.)", "AQL Level II, 1.0", 1,
         "Compare label against approved supplier list and PO", "BP / USP / Ph.Eur grade", "Per receipt"),
        ("A. Identification & Documentation", "3", "Expiry / Re-test date check", "AQL Level II, 1.0", 1,
         "Verify remaining shelf-life >= required usage period", "Min. 18 months remaining", "Per receipt"),
        ("B. Physical Appearance", "4", "Physical appearance (color, form)", "AQL Level II, 1.0", 1,
         "Inspect color and physical state vs. approved reference standard", "White / off-white powder", "Per receipt"),
        ("B. Physical Appearance", "5", "Odor", "AQL Level II, 1.0", 1,
         "Sniff test in fume hood; compare to reference description", "Odorless", "Per receipt"),
        ("B. Physical Appearance", "6", "Absence of foreign particles / contamination", "AQL Level II, 1.0", 1,
         "Inspect under adequate lighting for visible particulates, insects, etc.", "0 visible contaminants", "Per receipt"),
        ("B. Physical Appearance", "7", "Container integrity (no damage, seal intact)", "AQL Level II, 1.0", 1,
         "Check all containers for cracks, dents, broken seals or moisture ingress", "0 damage", "Per receipt"),
        ("C. Chemical / Assay Tests (Lab)", "8", "Identity test (IR / HPLC fingerprint)", "AQL Level II, 1.0", 1,
         "Run IR or HPLC per BP/USP monograph; compare to reference spectrum", "IR / HPLC match reference spectrum", "Per receipt"),
        ("C. Chemical / Assay Tests (Lab)", "9", "Assay / Potency", "AQL Level II, 1.0", 1,
         "HPLC assay per approved method", "98.0 - 101.5 %", "Per receipt"),
        ("C. Chemical / Assay Tests (Lab)", "10", "Loss on Drying (LOD) / Moisture content", "AQL Level II, 1.0", 1,
         "Dry at 105 C for 2 h; weigh before and after", "<= 0.5 %", "Per receipt"),
        ("C. Chemical / Assay Tests (Lab)", "11", "Residue on ignition / Sulphated ash", "AQL Level II, 1.0", 1,
         "Ignite in platinum crucible; weigh residue", "<= 0.1 %", "Per receipt"),
        ("C. Chemical / Assay Tests (Lab)", "12", "Heavy metals", "AQL Level II, 1.0", 1,
         "ICP-MS or colorimetric method per pharmacopeia", "<= 10 ppm", "Per receipt"),
        ("C. Chemical / Assay Tests (Lab)", "13", "Related substances / Impurity profile", "AQL Level II, 1.0", 1,
         "HPLC gradient method; compare to RRT impurity list", "Total impurities <= 0.5 %", "Per receipt"),
        ("C. Chemical / Assay Tests (Lab)", "14", "Microbial limit test (TAMC / TYMC)", "AQL Level II, 1.0", 1,
         "Membrane filtration or plate count per USP <61>", "TAMC <= 1000 CFU/g; TYMC <= 100 CFU/g", "Per receipt"),
        ("C. Chemical / Assay Tests (Lab)", "15", "Absence of specified microorganisms", "AQL Level II, 1.0", 1,
         "Selective enrichment per USP <62>", "Absent in 1 g", "Per receipt"),
        ("D. Physical Tests (Lab)", "16", "Particle size distribution (D50, D90)", "AQL Level II, 1.0", 1,
         "Laser diffraction (Malvern)", "D90 <= 250 um", "Per receipt"),
        ("D. Physical Tests (Lab)", "17", "Bulk / Tapped density", "AQL Level II, 1.0", 1,
         "Tap density tester per USP <616>", "Per approved specification", "Per receipt"),
        ("D. Physical Tests (Lab)", "18", "Solubility", "AQL Level II, 1.0", 1,
         "Visual solubility in water at 25 C per BP method", "Soluble / slightly soluble per spec", "Per receipt"),
        ("E. Storage & Disposition", "19", "Storage conditions verified (temp, humidity)", "AQL Level II, 1.0", 1,
         "Check temperature & RH loggers in storage area at time of receipt", "15-25 C, RH <= 60 %", "Per receipt"),
        ("E. Storage & Disposition", "20", "Quarantine label applied", "AQL Level II, 1.0", 1,
         "Attach yellow QUARANTINE label immediately on receipt", "Quarantine label present", "Per receipt"),
        ("E. Storage & Disposition", "21", "Release / Rejection label applied after QC decision", "AQL Level II, 1.0", 1,
         "Apply GREEN RELEASED or RED REJECTED label; update ERP/system", "Label = QC decision (PASS/FAIL)", "Per receipt"),
    ]

    # ── RM-002: Excipients Incoming QC (28 checks) ──
    checkpoints['RM-002'] = [
        ("A. Documentation", "1", "CoA / supplier documentation present", "AQL Level II, 1.0", 1,
         "Verify CoA; confirm grade, batch, expiry", "CoA batch no. = PO; approved supplier confirmed", "Per receipt"),
        ("A. Documentation", "2", "Approved supplier verification", "AQL Level II, 1.0", 1,
         "Cross-check supplier against Approved Supplier List (ASL)", "Supplier on ASL; 0 deviations", "Per receipt"),
        ("B. Physical Appearance", "3", "Appearance & color", "AQL Level II, 1.0", 1,
         "Compare to reference standard or specification sheet", "Per approved spec", "Per receipt"),
        ("B. Physical Appearance", "4", "Odor / taste (where applicable)", "AQL Level II, 1.0", 1,
         "Organoleptic check per monograph", "Characteristic per spec", "Per receipt"),
        ("B. Physical Appearance", "5", "Container integrity", "AQL Level II, 1.0", 1,
         "No damage, broken seals, signs of contamination", "0 damaged / broken seals", "Per receipt"),
        ("C. Tablet Excipients", "6", "MCC - Moisture (LOD)", "AQL Level II, 1.0", 1,
         "105 C / 3 h", "<= 5.0 %", "Per receipt"),
        ("C. Tablet Excipients", "7", "MCC - Particle size", "AQL Level II, 1.0", 1,
         "Sieve analysis", "Per grade spec (e.g., PH102)", "Per receipt"),
        ("C. Tablet Excipients", "8", "Lactose - Identity (IR)", "AQL Level II, 1.0", 1,
         "IR fingerprint vs. reference", "IR match reference spectrum", "Per receipt"),
        ("C. Tablet Excipients", "9", "Lactose - Optical rotation", "AQL Level II, 1.0", 1,
         "Polarimetry", "+54.4 to +55.9 degrees", "Per receipt"),
        ("C. Tablet Excipients", "10", "Magnesium Stearate - LOD", "AQL Level II, 1.0", 1,
         "105 C / 2 h", "<= 6.0 %", "Per receipt"),
        ("C. Tablet Excipients", "11", "Magnesium Stearate - Identity (IR)", "AQL Level II, 1.0", 1,
         "IR fingerprint vs. reference", "IR match reference spectrum", "Per receipt"),
        ("C. Tablet Excipients", "12", "Starch - Moisture", "AQL Level II, 1.0", 1,
         "105 C / 5 h", "<= 14.0 %", "Per receipt"),
        ("C. Tablet Excipients", "13", "PVP (Binder) - Viscosity / K-value", "AQL Level II, 1.0", 1,
         "Ubbelohde viscometer", "K30: 27 - 33 (per grade)", "Per receipt"),
        ("C. Tablet Excipients", "14", "HPMC (Coating) - Viscosity", "AQL Level II, 1.0", 1,
         "2 % aq. solution at 20 C", "Per grade spec", "Per receipt"),
        ("C. Tablet Excipients", "15", "Colorant - Identity (UV/Vis)", "AQL Level II, 1.0", 1,
         "Spectrophotometry vs. reference standard", "lambda-max = reference +/- 2 nm", "Per receipt"),
        ("D. Syrup Excipients", "16", "Sucrose - Appearance", "AQL Level II, 1.0", 1,
         "White crystalline powder or solution; no discoloration", "White; 0 foreign matter", "Per receipt"),
        ("D. Syrup Excipients", "17", "Sucrose - Specific rotation", "AQL Level II, 1.0", 1,
         "Polarimetry in water", "+66.3 to +67.0 degrees", "Per receipt"),
        ("D. Syrup Excipients", "18", "Sorbitol solution - Assay", "AQL Level II, 1.0", 1,
         "Enzymatic or HPLC method", "69.0 - 71.0 % w/w", "Per receipt"),
        ("D. Syrup Excipients", "19", "Methylparaben / Propylparaben - Assay (HPLC)", "AQL Level II, 1.0", 1,
         "HPLC vs. reference standard", "98.0 - 102.0 %", "Per receipt"),
        ("D. Syrup Excipients", "20", "Sodium Benzoate - Appearance & Assay", "AQL Level II, 1.0", 1,
         "Visual + titration or HPLC", ">= 99.0 % (dried basis)", "Per receipt"),
        ("D. Syrup Excipients", "21", "Propylene Glycol - Assay (GC)", "AQL Level II, 1.0", 1,
         "GC method per pharmacopeia", "99.0 - 101.0 %", "Per receipt"),
        ("D. Syrup Excipients", "22", "Flavor (liquid) - Appearance & Odor", "AQL Level II, 1.0", 1,
         "Organoleptic vs. reference standard sample", "True to type; 0 off-notes", "Per receipt"),
        ("D. Syrup Excipients", "23", "Purified Water - Conductivity", "AQL Level II, 1.0", 1,
         "Inline conductivity meter", "<= 1.3 uS/cm at 25 C", "Per receipt"),
        ("D. Syrup Excipients", "24", "Purified Water - TOC", "AQL Level II, 1.0", 1,
         "TOC analyser per USP <643>", "<= 500 ppb", "Per receipt"),
        ("D. Syrup Excipients", "25", "Purified Water - Microbial count", "AQL Level II, 1.0", 1,
         "Membrane filtration; R2A agar 30-35 C / 5 days", "<= 100 CFU/mL", "Per receipt"),
        ("E. Storage & Disposition", "26", "Quarantine label applied on receipt", "AQL Level II, 1.0", 1,
         "Yellow QUARANTINE label before testing", "Quarantine label present", "Per receipt"),
        ("E. Storage & Disposition", "27", "Storage condition verified", "AQL Level II, 1.0", 1,
         "Check area log or data-logger", "Per material spec (cold/ambient)", "Per receipt"),
        ("E. Storage & Disposition", "28", "Release / Rejection label after QC", "AQL Level II, 1.0", 1,
         "Green RELEASED or Red REJECTED label; update ERP", "Label = QC decision (PASS/FAIL)", "Per receipt"),
    ]

    # ── PM-001: Packaging Materials Incoming QC (24 checks) ──
    checkpoints['PM-001'] = [
        ("A. Documentation", "1", "CoA / supplier delivery note present", "AQL Level II, 1.0", 1,
         "Verify delivery note, CoA; check artwork version number", "Artwork version = approved master", "Per receipt"),
        ("A. Documentation", "2", "Artwork / print version verification", "AQL Level II, 1.0", 1,
         "Compare text, fonts, colors, barcodes to approved artwork master", "100 % match to approved artwork", "Per receipt"),
        ("A. Documentation", "3", "Barcode / 2D code scan verification", "AQL Level II, 1.0", 1,
         "Scan with barcode reader; confirm GTIN and lot code format", "GTIN reads correctly; 100 % read rate", "Per receipt"),
        ("B. Blister Foil & Lidding (Tablet)", "4", "Foil thickness", "AQL Level II, 1.0", 5,
         "Micrometer measurement at 5 points", "250 um +/- 10 um", "Per receipt"),
        ("B. Blister Foil & Lidding (Tablet)", "5", "Foil width", "AQL Level II, 1.0", 3,
         "Vernier caliper", "Per die dimension +/- 0.5 mm", "Per receipt"),
        ("B. Blister Foil & Lidding (Tablet)", "6", "Heat-seal strength (peel test)", "AQL Level II, 1.0", 1,
         "Peel tester at 200 mm/min; measure force", ">= 1.5 N/15 mm", "Per receipt"),
        ("B. Blister Foil & Lidding (Tablet)", "7", "Moisture vapor transmission rate (MVTR)", "AQL Level II, 1.0", 1,
         "Accept on CoA; audit test annually", "<= 0.5 g/m2/24h", "Per receipt"),
        ("B. Blister Foil & Lidding (Tablet)", "8", "Print / color consistency (pantone)", "AQL Level II, 1.0", 1,
         "Compare to approved color chip", "0 visible color deviation", "Per receipt"),
        ("B. Blister Foil & Lidding (Tablet)", "9", "Absence of pinholes / defects", "AQL Level II, 1.0", 1,
         "Back-light inspection of foil roll", "0 pinholes", "Per receipt"),
        ("C. Amber Glass Bottles (Syrup)", "10", "Bottle capacity / fill volume", "AQL Level II, 1.0", 5,
         "Fill with water; weigh or measure volume", "100 mL +/- 1 mL", "Per receipt"),
        ("C. Amber Glass Bottles (Syrup)", "11", "Wall thickness", "AQL Level II, 1.0", 4,
         "Micrometer at 4 points around shoulder", ">= 2.0 mm", "Per receipt"),
        ("C. Amber Glass Bottles (Syrup)", "12", "Neck finish / thread integrity", "AQL Level II, 1.0", 1,
         "Manual cap fit check; torque gauge", "0 leakage; 0 cross-threading", "Per receipt"),
        ("C. Amber Glass Bottles (Syrup)", "13", "Hydrolytic resistance (Class III glass)", "AQL Level II, 1.0", 1,
         "Accept on CoA; annual verification test", "Class III per Ph.Eur. 3.2.1", "Per receipt"),
        ("C. Amber Glass Bottles (Syrup)", "14", "Light transmission (amber glass)", "AQL Level II, 1.0", 1,
         "Spectrophotometric at 290-450 nm", "T <= 10 % at 290-450 nm", "Per receipt"),
        ("C. Amber Glass Bottles (Syrup)", "15", "Visual defect inspection (chips, cracks, bubbles)", "AQL Level II, 1.0", 1,
         "Visual inspection under bright light", "0 defects (chips / cracks / bubbles)", "Per receipt"),
        ("D. Caps / Closures", "16", "Cap diameter / fit", "AQL Level II, 1.0", 1,
         "Manual fit on bottle; torque gauge verification", "No leakage at 20 Ncm application", "Per receipt"),
        ("D. Caps / Closures", "17", "Child-resistant (CR) function", "AQL Level II, 1.0", 1,
         "Push-and-turn mechanism test per ISO 8317", "Opens with push-and-turn only", "Per receipt"),
        ("D. Caps / Closures", "18", "Liner / wad integrity", "AQL Level II, 1.0", 1,
         "Inspect liner for completeness, no tears", "Liner covers 100 % of bore", "Per receipt"),
        ("E. Outer Cartons & Inserts", "19", "Carton dimensions (L x W x H)", "AQL Level II, 1.0", 1,
         "Vernier caliper", "Per spec +/- 1 mm", "Per receipt"),
        ("E. Outer Cartons & Inserts", "20", "Carton crush / compression strength", "AQL Level II, 1.0", 1,
         "Compression tester", ">= 150 N", "Per receipt"),
        ("E. Outer Cartons & Inserts", "21", "Package insert text & version", "AQL Level II, 1.0", 1,
         "Check version code against approved master; read-through", "Text version = approved master", "Per receipt"),
        ("E. Outer Cartons & Inserts", "22", "Barcode on carton scans correctly", "AQL Level II, 1.0", 1,
         "Barcode scanner", "Correct GTIN; 100 % read rate", "Per receipt"),
        ("F. Storage & Disposition", "23", "Quarantine label applied on receipt", "AQL Level II, 1.0", 1,
         "Yellow QUARANTINE label before testing", "Quarantine label present", "Per receipt"),
        ("F. Storage & Disposition", "24", "Release / Rejection label after QC", "AQL Level II, 1.0", 1,
         "Green RELEASED or Red REJECTED label", "Label = QC decision (PASS/FAIL)", "Per receipt"),
    ]

    # ── IPQC-T-01: Granulation (6 checks) ──
    checkpoints['IPQC-T-01'] = [
        ("In-Process QC", "1", "Loss on Drying (LOD) - granule moisture", "AQL Level II, 1.0", 1,
         "Moisture analyser at 105 C / halogen; weigh before & after drying", "LOD <= 2.0 %", "Every 30 min during drying"),
        ("In-Process QC", "2", "Inlet / Outlet / Product bed temperature", "AQL Level II, 1.0", 3,
         "Read thermocouple display on FBD; record all three values", "Inlet: 60-70 C | Product bed: 40-50 C", "Every 15 min"),
        ("In-Process QC", "3", "Particle size after milling (visual / sieve)", "AQL Level II, 1.0", 1,
         "Sieve through 500 um mesh; record % retained vs. passed", ">= 90 % passes 500 um sieve", "After each milling batch"),
        ("In-Process QC", "4", "Bulk density", "AQL Level II, 1.0", 1,
         "Pour granules gently; record mass; calc. g/mL", "0.4 - 0.7 g/mL (typical)", "Per granulation batch"),
        ("In-Process QC", "5", "Tapped density / Hausner ratio", "AQL Level II, 1.0", 1,
         "Tap 500x; record tapped volume; Hausner = tapped / bulk", "Hausner ratio <= 1.25 (good flow)", "Per granulation batch"),
        ("In-Process QC", "6", "Blending uniformity (lubricant addition)", "AQL Level II, 1.0", 3,
         "Sample at 3 points of blender after Mg-Stearate addition; weigh micro-sample", "Assay RSD <= 2 % across positions", "After each blending step"),
    ]

    # ── IPQC-T-02: Compression (10 checks) ──
    checkpoints['IPQC-T-02'] = [
        ("In-Process QC", "1", "Individual tablet weight", "20 tablets / check", 20,
         "Weigh each tablet individually on analytical balance; calc mean & RSD", "600 mg +/- 5 % | RSD <= 2 %", "Every 30 min + start & end of run"),
        ("In-Process QC", "2", "Weight of 20 tablets (bulk check)", "1 x 20-tablet sample", 1,
         "Weigh 20 tablets together; divide by 20 = mean weight", "Mean = 600 mg +/- 5 %", "Every 60 min"),
        ("In-Process QC", "3", "Tablet thickness", "10 tablets / check", 10,
         "Thickness gauge on each tablet; record min, max, mean", "5.0 mm +/- 5 % (4.75 - 5.25 mm)", "Every 30 min"),
        ("In-Process QC", "4", "Tablet diameter", "10 tablets / check", 10,
         "Vernier caliper on each tablet; record min, max, mean", "14.0 mm +/- 5 % (13.3 - 14.7 mm)", "Every 30 min"),
        ("In-Process QC", "5", "Tablet hardness (crush strength)", "10 tablets / check", 10,
         "Place tablet flat in hardness tester; record force at breakage (Newtons)", "80 - 160 N", "Every 30 min"),
        ("In-Process QC", "6", "Friability", "20 tablets (pre-weighed)", 1,
         "Drum at 25 rpm x 100 rotations (4 min); re-weigh; % loss = (W0-W1)/W0 x 100", "% weight loss <= 1.0 %", "Once per batch (start of run)"),
        ("In-Process QC", "7", "Disintegration time", "6 tablets", 6,
         "USP disintegration apparatus, 900 mL water at 37 C +/- 0.5 C, no discs", "All 6 tablets disintegrate in <= 15 minutes", "Every 2 hours"),
        ("In-Process QC", "8", "Tablet color & surface appearance", "Visual, all tablets on belt or tray", 1,
         "Inspect for correct color (white/off-white), no cracks, chips, sticking", "No capping, lamination, sticking or mottling", "Continuous / every 30 min"),
        ("In-Process QC", "9", "Tablet de-dusting efficiency", "Visual check on de-duster output", 1,
         "Ensure no excess powder on tablet surface after de-duster", "Clean surface; no visible dust layer", "Every 60 min"),
        ("In-Process QC", "10", "Punch/die condition check", "Tooling inspection", 1,
         "Stop press; visually inspect upper & lower punches for wear, chipping, sticking", "No worn/damaged punches allowed", "Every 4 hours or at changeover"),
    ]

    # ── IPQC-T-03: Coating & Blistering (8 checks) ──
    checkpoints['IPQC-T-03'] = [
        ("In-Process QC", "1", "Tablet weight gain (coating build-up)", "20 tablets / check", 20,
         "Weigh 20 tablets before coating and periodically during; % gain = (Wn-W0)/W0 x 100", "Target weight gain: 2 - 4 % of core weight", "Every 30 min during coating"),
        ("In-Process QC", "2", "Coating pan temperature - inlet / outlet", "Continuous logger", 1,
         "Read thermocouple; record inlet and outlet air temperature", "Inlet: 55-65 C | Outlet: 40-50 C", "Every 15 min"),
        ("In-Process QC", "3", "Film uniformity & color consistency", "Visual, 20-tablet sample", 20,
         "Compare coated tablets to approved color standard; check for twin-tablets, chipping", "Uniform coat; no peeling, chipping, twinning or bridging", "Every 30 min"),
        ("In-Process QC", "4", "Logo / break-line embossing clarity", "10 tablets", 10,
         "Compare to approved artwork master under magnifying lamp", "Logo clearly legible; break-line depth consistent", "Every 60 min"),
        ("In-Process QC", "5", "Blister seal integrity (bubble test)", "3 blister strips / check", 3,
         "Submerge sealed blister in coloured water; apply gentle pressure; observe bubbles", "Zero bubbles = Pass; any bubble = Fail (Critical)", "Every 30 min during blistering"),
        ("In-Process QC", "6", "Blister peel force", "5 strips / check", 5,
         "Peel tester at 180 degree angle, 300 mm/min pull speed", "2 - 4 N/cm", "Every 60 min"),
        ("In-Process QC", "7", "PVC/PVDC foil thickness", "3 samples / roll change", 3,
         "Thickness gauge at 5 points on a cut section", "PVC: 250 um +/- 10% | PVDC: 60 g/m2 +/- 10%", "At each foil roll change"),
        ("In-Process QC", "8", "Tablet count per blister cavity", "Visual, every 10th blister card", 1,
         "Count tablets in each pocket; verify none missing or duplicated", "Correct count per design (e.g., 10 tablets/strip)", "Continuous / every 10th card"),
    ]

    # ── IPQC-S-01: Mixing & Dissolution (13 checks) ──
    checkpoints['IPQC-S-01'] = [
        ("In-Process QC", "1", "Purified water conductivity", "AQL Level II, 1.0", 1,
         "Read inline conductivity meter at PW outlet point", "<= 1.3 uS/cm at 25 C", "Before every batch"),
        ("In-Process QC", "2", "Purified water TOC", "AQL Level II, 1.0", 1,
         "TOC analyser per USP <643>; collect 50 mL sample", "<= 500 ppb", "Daily / before use"),
        ("In-Process QC", "3", "Purified water microbial count", "AQL Level II, 1.0", 1,
         "Membrane filtration; R2A agar 30-35 C / 5 days", "<= 100 CFU/mL", "Weekly"),
        ("In-Process QC", "4", "API (Paracetamol) complete dissolution", "AQL Level II, 1.0", 1,
         "Stir at 60-70 C; inspect against back-lit white background", "No visible undissolved particles; clear solution", "After each dissolution step"),
        ("In-Process QC", "5", "Mixing temperature", "AQL Level II, 1.0", 1,
         "Read thermometer in vessel jacket or product; record every 15 min", "60 - 70 C during dissolution stage", "Every 15 min"),
        ("In-Process QC", "6", "Mixing duration compliance", "AQL Level II, 1.0", 1,
         "Record actual start & stop time of mixing; compare to batch record SOP", "Per approved batch record (typically 30-60 min)", "Per batch"),
        ("In-Process QC", "7", "Sucrose Brix / concentration", "AQL Level II, 1.0", 1,
         "Refractometer reading at 20 C on diluted sample", "60 - 65 Brix (or per batch formula)", "After sucrose addition"),
        ("In-Process QC", "8", "Sorbitol addition weight check", "AQL Level II, 1.0", 1,
         "Confirm actual weight of sorbitol added vs. batch record", "Batch record quantity +/- 0.5 %", "At time of addition"),
        ("In-Process QC", "9", "pH of bulk syrup (hot, pre-cool)", "AQL Level II, 1.0", 1,
         "Calibrated pH meter (buffer pH 4.0 & 7.0); measure in vessel after mixing", "3.5 - 5.5", "After mixing; before cooling"),
        ("In-Process QC", "10", "pH of bulk syrup (cooled, final)", "AQL Level II, 1.0", 1,
         "Same pH meter; measure when bulk reaches 25 C +/- 2 C", "3.5 - 5.5 (adjust with citric acid / NaOH if needed)", "After cooling to ambient"),
        ("In-Process QC", "11", "Methylparaben / Propylparaben weight", "AQL Level II, 1.0", 1,
         "Confirm actual weight of preservatives added vs. batch formula", "Batch record quantity +/- 0.5 %", "At time of addition"),
        ("In-Process QC", "12", "Flavour addition weight", "AQL Level II, 1.0", 1,
         "Confirm actual weight of flavour (cherry/strawberry) vs. batch formula", "Batch record quantity +/- 0.5 %", "At time of addition"),
        ("In-Process QC", "13", "Organoleptic check (odour / taste)", "AQL Level II, 1.0", 1,
         "Smell and taste small sample; compare to reference standard or previous approved batch", "True to flavour profile; no off-notes or chemical smell", "After flavour addition"),
    ]

    # ── IPQC-S-02: Physical-Chemical (11 checks) ──
    checkpoints['IPQC-S-02'] = [
        ("In-Process QC", "1", "Visual appearance - colour", "3 samples vs. std", 3,
         "Compare against approved colour standard (pale pink/red); use white background", "Matches approved colour standard; no discolouration", "After mixing; after cooling"),
        ("In-Process QC", "2", "Clarity / absence of particles", "3 samples, light box", 3,
         "Inspect 20 mL in glass vial against white AND black background under lamp", "Clear; no visible particulates, fibres, or cloudiness", "After mixing; after cooling"),
        ("In-Process QC", "3", "Turbidity (NTU)", "1 composite sample", 1,
         "Nephelometer reading on filtered sample at 25 C", "<= 5 NTU", "Per batch"),
        ("In-Process QC", "4", "Final bulk pH", "3 readings", 3,
         "Calibrated pH meter (2-point cal. pH 4.0 & 7.0) at 25 C +/- 2 C", "3.5 - 5.5", "After every adjustment; final check"),
        ("In-Process QC", "5", "pH after preservative addition", "3 readings", 3,
         "Re-check pH after adding parabens (they can shift pH slightly)", "3.5 - 5.5 (no change > 0.3 units)", "After preservative addition"),
        ("In-Process QC", "6", "Viscosity (dynamic)", "2 samples at 25 C", 2,
         "Brookfield LV Viscometer; spindle selection per SOP; read at equilibrium", "50 - 200 mPa.s at 25 C", "Per batch; after cooling to 25 C"),
        ("In-Process QC", "7", "Specific gravity", "Pycnometer or densitometer, 25 C", 1,
         "Fill pycnometer; weigh; compare to water reference", "1.10 - 1.30 g/mL (typical for sucrose syrup)", "Per batch"),
        ("In-Process QC", "8", "Paracetamol assay - in-process HPLC", "1 composite sample, 10 mL", 1,
         "HPLC per USP/BP monograph; dilute per SOP; run vs. reference standard", "95.0 - 105.0 % of 120 mg/5 mL label claim", "Once per batch before filling"),
        ("In-Process QC", "9", "Content uniformity across tank (top/mid/bottom)", "3 samples", 3,
         "HPLC on samples taken from top, middle and bottom of mixing tank", "RSD <= 2.0 % across 3 sampling points", "After mixing, before filling"),
        ("In-Process QC", "10", "Total Aerobic Microbial Count (TAMC)", "1 x 10 mL sample", 1,
         "Membrane filtration; SCDA agar 30-35 C / 5 days", "<= 100 CFU/mL", "Per batch (results before release)"),
        ("In-Process QC", "11", "Absence of Pseudomonas aeruginosa", "1 x 10 mL sample", 1,
         "Selective enrichment per USP <62>", "Absent in 10 mL", "Per batch"),
    ]

    # ── IPQC-S-03: Filling & Capping (17 checks) ──
    checkpoints['IPQC-S-03'] = [
        ("In-Process QC", "1", "Fill volume - gravimetric check", "10 bottles / check", 10,
         "Weigh empty bottle (tare); fill; weigh again. Volume = net weight / specific gravity", "100 mL +/- 2 mL (98 - 102 mL)", "Start, every 30 min, end of run"),
        ("In-Process QC", "2", "Fill volume - visual check (graduated cylinder)", "3 bottles / check", 3,
         "Pour bottle contents into graduated cylinder; read meniscus at eye level", "100 mL +/- 2 mL", "Every 60 min as supplementary check"),
        ("In-Process QC", "3", "Syrup temperature at filling head", "Probe reading", 1,
         "Read thermocouple at filling nozzle; hot-fill processes require specific range", "Ambient fill: 20-30 C | Hot-fill: per SOP", "Every 30 min"),
        ("In-Process QC", "4", "Cap application torque (closing)", "5 bottles / check", 5,
         "Cap torque meter; measure closing torque applied by capping machine", "20 - 40 Ncm (or per cap supplier spec)", "Every 30 min"),
        ("In-Process QC", "5", "Cap removal torque (opening)", "5 bottles / check", 5,
         "Cap torque meter; consumer should be able to open; CR cap must resist child", "10 - 30 Ncm (child-resistant spec)", "Every 30 min"),
        ("In-Process QC", "6", "Leak test (invert bottle)", "5 bottles / check", 5,
         "Invert capped bottle for 2 min on paper towel; inspect for syrup leakage", "Zero leakage", "Every 30 min"),
        ("In-Process QC", "7", "Cap seal / induction liner integrity", "5 bottles", 5,
         "Visual inspection for liner presence; after induction sealer, check bond", "Liner fully bonded; no lifted edges", "After each induction seal cycle"),
        ("In-Process QC", "8", "Label alignment & placement", "5 bottles / check", 5,
         "Visual and ruler check; label must be straight, centred, no air bubbles", "Position tolerance +/- 2 mm", "Every 30 min"),
        ("In-Process QC", "9", "Printed lot number correctness", "5 bottles / check", 5,
         "Read printed lot number; compare to batch record", "Matches batch record exactly", "Every 30 min"),
        ("In-Process QC", "10", "Printed expiry date correctness", "5 bottles / check", 5,
         "Read printed expiry date; compare to approved shelf-life calculation", "Correct date; legible; not smudged", "Every 30 min"),
        ("In-Process QC", "11", "Barcode / 2D code scan", "5 bottles / check", 5,
         "Scan with barcode reader; confirm GTIN and lot code decode correctly", "100 % read rate; correct GTIN", "Every 30 min"),
        ("In-Process QC", "12", "Amber bottle colour uniformity", "Visual, 5 bottles", 5,
         "Compare to approved bottle standard; check UV-blocking amber shade", "Uniform amber; no clear sections", "Per bottle batch / start of run"),
        ("In-Process QC", "13", "Bottle integrity (cracks, chips)", "100 % inline or AQL", 1,
         "Visual inspection on conveyor or by camera; reject any damaged bottle", "Zero cracks, chips, deformations", "Continuous / 100 % inspection"),
        ("In-Process QC", "14", "Bottle cleanliness (inversion / air-rinse)", "5 bottles / check", 5,
         "Inspect after bottle inversion rinser; no particles, dust, or water inside", "Clean interior; no foreign matter", "Every 60 min"),
        ("In-Process QC", "15", "Reconciliation - bottles filled vs. issued", "Count", 1,
         "Count filled bottles + rejects + empties remaining = total issued", "Reconciliation >= 99.5 %", "End of batch"),
        ("In-Process QC", "16", "Label reconciliation", "Count", 1,
         "Labels used + damaged + returned = total issued", "Reconciliation >= 99.5 %", "End of batch"),
        ("In-Process QC", "17", "Line clearance - no previous batch material", "Visual", 1,
         "Inspect filling line, capping machine, conveyors for previous labels/bottles", "Zero previous-batch items present", "Before next batch start"),
    ]

    # ── FP-TAB-500: Finished Product Release - Tablet (33 checks) ──
    checkpoints['FP-TAB-500'] = [
        ("1. Physical & Visual Tests", "1", "Tablet colour", "AQL Level II, 1.0", 1,
         "Visual inspection against approved colour standard; back-lit white background", "White to off-white; uniform, no discolouration", "Per batch"),
        ("1. Physical & Visual Tests", "2", "Tablet shape & surface", "AQL Level II, 1.0", 1,
         "Visual inspection; rate each defect type", "Round, biconvex; no capping / lamination / chipping / sticking", "Per batch"),
        ("1. Physical & Visual Tests", "3", "Tablet dimensions - thickness", "AQL Level II, 1.0", 10,
         "Thickness gauge; record min, max, mean of 10 tablets", "5.0 mm +/- 5 % (4.75 - 5.25 mm)", "Per batch"),
        ("1. Physical & Visual Tests", "4", "Tablet dimensions - diameter", "AQL Level II, 1.0", 10,
         "Vernier caliper; record min, max, mean of 10 tablets", "14.0 mm +/- 5 % (13.3 - 14.7 mm)", "Per batch"),
        ("1. Physical & Visual Tests", "5", "Individual tablet weight", "AQL Level II, 1.0", 20,
         "Weigh each of 20 tablets individually; calculate mean & RSD", "600 mg +/- 5 % (570 - 630 mg); RSD <= 2.0 %", "Per batch"),
        ("1. Physical & Visual Tests", "6", "Film coat uniformity & appearance", "AQL Level II, 1.0", 20,
         "Visual inspection + gravimetric weight gain check", "Uniform coat; no peeling/blistering/twinning; coat weight gain 2-4 %", "Per batch"),
        ("2. Mechanical Tests", "7", "Tablet hardness (crush strength)", "AQL Level II, 1.0", 10,
         "Hardness tester; place tablet flat; record force at fracture (Newtons)", "80 - 160 N", "Per batch"),
        ("2. Mechanical Tests", "8", "Friability", "AQL Level II, 1.0", 1,
         "Roche friabilator at 25 rpm x 100 rotations; de-dust; re-weigh", "% weight loss <= 1.0 %", "Per batch"),
        ("2. Mechanical Tests", "9", "Disintegration time", "AQL Level II, 1.0", 6,
         "USP disintegration apparatus; 900 mL purified water at 37 C +/- 0.5 C; no discs", "All 6 tablets disintegrate in <= 15 minutes", "Per batch"),
        ("3. Chemical / Analytical Tests", "10", "Dissolution rate", "AQL Level II, 1.0", 6,
         "USP apparatus II (paddle), 900 mL phosphate buffer pH 5.8, 50 rpm, 37 C; HPLC or UV assay at 30 min", ">= 80 % of label claim dissolved in 30 minutes (Q = 80 %)", "Per batch"),
        ("3. Chemical / Analytical Tests", "11", "Assay / Potency (Paracetamol)", "AQL Level II, 1.0", 1,
         "HPLC per BP/USP monograph; dissolve composite in mobile phase; inject vs. reference standard", "95.0 % - 105.0 % of 500 mg label claim", "Per batch"),
        ("3. Chemical / Analytical Tests", "12", "Content uniformity", "AQL Level II, 1.0", 10,
         "HPLC assay on each of 10 individual tablets per USP <905>", "Each unit: 85.0-115.0 % of label claim; RSD <= 6.0 %", "Per batch"),
        ("3. Chemical / Analytical Tests", "13", "Related substances / impurities", "AQL Level II, 1.0", 1,
         "HPLC gradient method per ICH Q3B; compare to RRT impurity list", "Any individual impurity <= 0.2 %; total impurities <= 0.5 %", "Per batch"),
        ("3. Chemical / Analytical Tests", "14", "Microbial limit test (TAMC / TYMC)", "AQL Level II, 1.0", 1,
         "Membrane filtration per USP <61>; SCDA agar 30-35 C / 5 days", "TAMC <= 1000 CFU/g; TYMC <= 100 CFU/g; No E. coli in 1 g", "Per batch"),
        ("4. Packaging Integrity", "15", "Blister seal integrity (bubble test)", "AQL Level II, 1.0", 3,
         "Submerge sealed blister in coloured water under gentle pressure; observe for bubbles", "Zero bubbles from any cavity = Pass", "Per batch"),
        ("4. Packaging Integrity", "16", "Blister peel force", "AQL Level II, 1.0", 5,
         "Peel tester at 180 degree angle, 300 mm/min pull speed", "2.0 - 4.0 N/cm", "Per batch"),
        ("4. Packaging Integrity", "17", "Blister foil thickness (PVC/PVDC)", "AQL Level II, 1.0", 5,
         "Thickness gauge at 5 points on cut section", "PVC: 250 um +/- 10 %; PVDC: 60 g/m2 +/- 10 %", "Per batch"),
        ("4. Packaging Integrity", "18", "Child-resistance performance (ISO 8317)", "AQL Level II, 1.0", 1,
         "ISO 8317 panel test protocol", "Child fail rate >= 80 %; Adult success rate >= 85 %", "Per batch"),
        ("4. Packaging Integrity", "19", "Carton dimensions", "AQL Level II, 1.0", 5,
         "Vernier caliper", "50 x 90 x 18 mm +/- 1 mm", "Per batch"),
        ("4. Packaging Integrity", "20", "Carton seal / closure integrity", "AQL Level II, 1.0", 5,
         "Manual tug test + visual; pull all flaps", "No open flaps; glue holds under 5 N pull", "Per batch"),
        ("4. Packaging Integrity", "21", "Shipping box compression strength", "AQL Level II, 1.0", 1,
         "ASTM D4169 compression test", "Withstands >= 200 kg vertical load", "Per batch"),
        ("4. Packaging Integrity", "22", "Shipping box dimensions & fill count", "AQL Level II, 1.0", 1,
         "Tape measure + manual count of cartons inside", "200 x 200 x 150 mm +/- 2 mm; 10 cartons per box", "Per batch"),
        ("5. Labelling & Regulatory", "23", "Product name legibility", "5 units, AQL II", 5,
         "Visual vs. approved artwork master", "Fully legible; correct font, size & colour per artwork", "Per batch"),
        ("5. Labelling & Regulatory", "24", "Active ingredient & strength", "6 units, AQL II", 6,
         "Visual + content check vs. approved artwork", "Paracetamol 500 mg stated clearly; no truncation", "Per batch"),
        ("5. Labelling & Regulatory", "25", "Batch number format & readability", "7 units, AQL II", 7,
         "Visual inspection; decode format", "Format: PARA-T-YYYYMMDD-001; fully legible; not smudged", "Per batch"),
        ("5. Labelling & Regulatory", "26", "Manufacturing & expiry dates", "8 units, AQL II", 8,
         "Visual + date logic: Mfg <= today; Exp = Mfg + shelf-life", "Correct dates in DD/MM/YYYY format; shelf-life 24-36 months", "Per batch"),
        ("5. Labelling & Regulatory", "27", "Dosage instructions accuracy", "9 units, AQL II", 9,
         "Compare to approved SPC / PIL", "Instructions match approved Summary of Product Characteristics exactly", "Per batch"),
        ("5. Labelling & Regulatory", "28", "Storage conditions statement", "10 units, AQL II", 10,
         "Visual check vs. approved label", "Store below 25 C; keep dry; protect from light - stated clearly", "Per batch"),
        ("5. Labelling & Regulatory", "29", "Turkish language compliance (TSE)", "11 units, AQL II", 11,
         "Review by Turkish-speaking QC staff against TSE requirements", "All mandatory fields in Turkish as primary language; no translation errors", "Per batch"),
        ("5. Labelling & Regulatory", "30", "Manufacturer name & address", "12 units, AQL II", 12,
         "Visual vs. approved artwork", "Atlas Pharma name, address, country of manufacture printed clearly", "Per batch"),
        ("5. Labelling & Regulatory", "31", "Barcode scan quality (GS1-128)", "13 units, AQL II", 13,
         "GS1 barcode verifier per ISO/IEC 15416", "Grade C or above; correct GTIN encoded and decoded", "Per batch"),
        ("5. Labelling & Regulatory", "32", "Pictogram & warning symbols", "14 units, AQL II", 14,
         "Visual check vs. approved artwork", "Keep out of reach of children symbol + all required pictograms present", "Per batch"),
        ("5. Labelling & Regulatory", "33", "Over-labelling / double labelling", "15 units, AQL II", 15,
         "Visual during packaging line run", "Zero double labels; zero misaligned labels", "Per batch"),
    ]

    # ── FP-SYP-125: Finished Product Release - Syrup (37 checks) ──
    checkpoints['FP-SYP-125'] = [
        ("1. Physical & Organoleptic Tests", "1", "Syrup appearance - colour", "1 bottle / 10 from batch", 1,
         "Visual against white AND black background under adequate lighting", "Clear to pale pink/red; colour matches approved standard", "Per batch"),
        ("1. Physical & Organoleptic Tests", "2", "Syrup clarity / absence of particles", "1 bottle / 10 from batch", 1,
         "Inspect 20 mL in glass vial against white AND black background under lamp", "Clear; no visible particles, fibres, haziness, or cloudiness", "Per batch"),
        ("1. Physical & Organoleptic Tests", "3", "Flavour / odour acceptability", "Sensory panel, 3 evaluators", 3,
         "Organoleptic evaluation; compare to reference standard sample", "Cherry/strawberry flavour true to type; no off-odour or chemical notes", "Per batch"),
        ("1. Physical & Organoleptic Tests", "4", "Sediment / sedimentation stability", "Stored sample, 24 h rest", 1,
         "Shake vigorously; let stand 24 h; inspect for hard sediment cake", "No hard cake; resuspends within 30 seconds of shaking", "Per batch"),
        ("2. Physical-Chemical Tests", "5", "pH measurement", "3 bottles / batch", 3,
         "Calibrated pH meter (2-point calibration pH 4.0 & 7.0) at 25 C +/- 2 C", "3.5 - 5.5", "Per batch"),
        ("2. Physical-Chemical Tests", "6", "Viscosity", "2 samples / batch at 25 C", 2,
         "Brookfield LV viscometer; spindle per SOP; read at equilibrium", "50 - 200 mPa.s at 25 C", "Per batch"),
        ("2. Physical-Chemical Tests", "7", "Volume fill accuracy", "10 bottles / batch", 10,
         "Gravimetric check: net weight / specific gravity = volume (mL)", "100 mL +/- 2 mL (98 - 102 mL)", "Per batch"),
        ("3. Chemical / Analytical Tests", "8", "Assay / Potency (Paracetamol)", "3 composite samples / batch", 3,
         "HPLC per BP/USP monograph; dilute per SOP; inject vs. reference standard", "95.0 % - 105.0 % of 120 mg/5 mL label claim", "Per batch"),
        ("3. Chemical / Analytical Tests", "9", "Content uniformity across batch", "10 bottles (top, middle, bottom of tank)", 10,
         "HPLC on individual bottles from 3 sampling positions", "RSD <= 2.0 % across sampled bottles", "Per batch"),
        ("3. Chemical / Analytical Tests", "10", "Related substances / impurities", "1 composite sample / batch", 1,
         "HPLC gradient method per ICH Q3B", "Any individual impurity <= 0.2 %; total impurities <= 0.5 %", "Per batch"),
        ("3. Chemical / Analytical Tests", "11", "Preservative efficacy test", "1 sample / batch (stability)", 1,
         "USP <51> Antimicrobial Effectiveness Test", "Meets Category 3 criteria (oral liquids) - no increase in count after 14 days", "Per batch"),
        ("4. Microbial Tests", "12", "Total Aerobic Microbial Count (TAMC)", "3 bottles / batch", 3,
         "Membrane filtration per USP <61>; SCDA agar 30-35 C / 5 days", "TAMC <= 100 CFU/mL", "Per batch"),
        ("4. Microbial Tests", "13", "Total Yeast & Mould Count (TYMC)", "3 bottles / batch", 3,
         "Membrane filtration; SDA agar 20-25 C / 5 days", "TYMC <= 10 CFU/mL", "Per batch"),
        ("4. Microbial Tests", "14", "Absence of Pseudomonas aeruginosa", "3 bottles / batch", 3,
         "Selective enrichment per USP <62>", "Absent in 1 mL", "Per batch"),
        ("4. Microbial Tests", "15", "Absence of E. coli", "3 bottles / batch", 3,
         "Selective enrichment per USP <62>", "Absent in 1 mL", "Per batch"),
        ("5. Packaging Integrity", "16", "Amber bottle integrity (cracks, chips)", "5 bottles / batch, AQL II", 5,
         "Visual + light-box inspection; compress bottle slightly", "No cracks, chips, deformations; amber colour uniform", "Per batch"),
        ("5. Packaging Integrity", "17", "Child-resistant cap - closing torque", "5 bottles / batch", 5,
         "Cap torque meter (closing)", "20 - 40 Ncm", "Per batch"),
        ("5. Packaging Integrity", "18", "Child-resistant cap - opening torque", "5 bottles / batch", 5,
         "Cap torque meter (opening / consumer open)", "10 - 30 Ncm (must resist child per ISO 8317)", "Per batch"),
        ("5. Packaging Integrity", "19", "Leak test (inverted bottle)", "5 bottles / batch", 5,
         "Invert capped bottle on absorbent paper for 2 min; inspect for leakage", "Zero leakage", "Per batch"),
        ("5. Packaging Integrity", "20", "Child-resistance performance (ISO 8317)", "Type test - 50 children / 100 adults", 1,
         "ISO 8317 panel test protocol", "Child fail rate >= 80 %; Adult success rate >= 85 %", "Per batch"),
        ("5. Packaging Integrity", "21", "Measuring spoon inclusion", "100 % of syrup cartons", 1,
         "Visual check during line inspection", "1 x 5 mL measuring spoon per carton; correct 5 mL graduation marking", "Per batch"),
        ("5. Packaging Integrity", "22", "Carton dimensions", "5 cartons / batch", 5,
         "Vernier caliper", "55 x 55 x 120 mm +/- 1 mm", "Per batch"),
        ("5. Packaging Integrity", "23", "Carton seal / closure integrity", "10 cartons / batch", 10,
         "Manual tug test + visual", "No open flaps; glue holds under 5 N pull", "Per batch"),
        ("5. Packaging Integrity", "24", "Shipping box compression strength", "1 box per type test", 1,
         "ASTM D4169 compression test", "Withstands >= 200 kg vertical load", "Per batch"),
        ("5. Packaging Integrity", "25", "Shipping box dimensions & fill count", "3 boxes / batch", 3,
         "Tape measure + manual count of cartons inside", "200 x 200 x 150 mm +/- 2 mm; 10 cartons per box", "Per batch"),
        ("6. Labelling & Regulatory", "26", "Product name legibility", "5 units / batch", 5,
         "Visual vs. approved artwork master", "Fully legible; correct font, size & colour per artwork", "Per batch"),
        ("6. Labelling & Regulatory", "27", "Active ingredient & strength", "5 units / batch", 5,
         "Visual + content check vs. approved artwork", "Paracetamol 120 mg/5 mL stated clearly; no truncation", "Per batch"),
        ("6. Labelling & Regulatory", "28", "Batch number format & readability", "10 units / batch", 10,
         "Visual inspection; decode format", "Format: PARA-S-YYYYMMDD-001; fully legible; not smudged", "Per batch"),
        ("6. Labelling & Regulatory", "29", "Manufacturing & expiry dates", "10 units / batch", 10,
         "Visual + date logic: Mfg <= today; Exp = Mfg + shelf-life", "Correct dates in DD/MM/YYYY format; shelf-life 24 months", "Per batch"),
        ("6. Labelling & Regulatory", "30", "Dosage instructions accuracy", "5 units / batch", 5,
         "Compare to approved SPC / PIL", "Instructions match approved SPC; includes paediatric dosing table", "Per batch"),
        ("6. Labelling & Regulatory", "31", "Storage conditions statement", "5 units / batch", 5,
         "Visual check vs. approved label", "Store below 25 C; protect from light; keep out of reach of children", "Per batch"),
        ("6. Labelling & Regulatory", "32", "Turkish language compliance (TSE)", "5 units / batch", 5,
         "Review by Turkish-speaking QC staff against TSE requirements", "All mandatory fields in Turkish as primary language; no translation errors", "Per batch"),
        ("6. Labelling & Regulatory", "33", "Manufacturer name & address", "5 units / batch", 5,
         "Visual vs. approved artwork", "Atlas Pharma name, address, country of manufacture printed clearly", "Per batch"),
        ("6. Labelling & Regulatory", "34", "Barcode scan quality (GS1-128)", "10 units / batch", 10,
         "GS1 barcode verifier per ISO/IEC 15416", "Grade C or above; correct GTIN encoded and decoded", "Per batch"),
        ("6. Labelling & Regulatory", "35", "Label adhesion (amber bottle)", "5 bottles / batch", 5,
         "Peel test at 90 degree angle after 24 h application; check adhesive strength", "No peeling, lifting or bubbling after 24 h", "Per batch"),
        ("6. Labelling & Regulatory", "36", "Pictogram & warning symbols", "5 units / batch", 5,
         "Visual check vs. approved artwork", "Keep out of reach of children + all required pictograms present", "Per batch"),
        ("6. Labelling & Regulatory", "37", "Over-labelling / double labelling", "100 % inline inspection", 1,
         "Visual during packaging line run", "Zero double labels; zero misaligned labels", "Per batch"),
    ]

    # Insert all checkpoints
    for stage_code, checks in checkpoints.items():
        stage_id = sid.get(stage_code)
        if not stage_id:
            continue
        for c in checks:
            conn.execute(
                """INSERT INTO stage_checkpoints
                   (stage_id, section, checkpoint_no, checkpoint_name, sample_size,
                    sample_count, instruction, tolerance, frequency)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (stage_id, c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7]),
            )

    # ── Auto-classify result_type ─────────────────────────────────────────────
    # Rules: passfail = visual/doc checks; numeric = measured values with units
    def _classify(name, tolerance, section):
        n = (name or '').lower()
        t = (tolerance or '').lower()
        s = (section or '').lower()

        # Section-level overrides → passfail
        if any(kw in s for kw in ('documentation', 'disposition', 'appearance')):
            return 'passfail'

        # Tolerance-level passfail patterns
        tol_pf = (
            'absent', '0 damage', '0 visible', '0 defect', '0 pinhole',
            'zero ', 'quarantine label', 'label = qc', 'match reference',
            'ir match', 'ir / hplc match', '100 % match', 'no leakage',
            'no capping', 'true to', 'class iii', 'reads correctly',
            'matches batch', 'correct count', 'conforms', '0 leakage',
            '0 cross', '100 % read', 'liner covers', 'opens with',
            'matches approved', 'approved colour', '0 bubbles',
            'uniform coat', 'no peeling', 'clearly legible', 'no visible',
            'clean surface', 'no worn', 'pass/fail', 'prior batch',
            'zero previous', 'artwork version', 'gtin reads', 'text version',
            'clean interior', 'no previous', 'soluble', 'no off-notes',
            'no foreign', 'characteristic per', 'true to flavour',
            'per approved', 'label present', '0 foreign', 'label correct',
            'no visible undissolved', 'per batch record', 'no change >',
            'fully bonded', 'correct date', 'legible', 'uniform amber',
            'zero cracks', 'zero bubbles', 'zero leakage'
        )
        if any(kw in t for kw in tol_pf):
            return 'passfail'

        # Name-level passfail patterns
        name_pf = (
            'verif', 'applied', 'reconcil', 'clearance', 'absence of',
            'integrity', 'organolep', 'seal integr', 'label alignment',
            'label reconcil', 'line clearance', 'child-resist', 'cr function',
            'visual defect', 'visual check', 'print / color', 'print/color',
            'colour uniformity', 'colour consistency', 'film uniformity',
            'logo / break', 'tablet count per', 'de-dusting', 'punch/die',
            'bottle cleanliness', 'cap seal', 'printed lot', 'printed expiry',
            'barcode / 2d', 'bottle integrity', 'amber bottle colour',
            'cap application', 'cap removal', 'leak test', 'dissolution check'
        )
        if any(kw in n for kw in name_pf):
            return 'passfail'

        return 'numeric'

    all_cp = conn.execute(
        "SELECT id, checkpoint_name, tolerance, section FROM stage_checkpoints"
    ).fetchall()
    for cp in all_cp:
        rtype = _classify(cp['checkpoint_name'], cp['tolerance'], cp['section'])
        conn.execute(
            "UPDATE stage_checkpoints SET result_type = ? WHERE id = ?",
            (rtype, cp['id'])
        )

    conn.commit()
    conn.close()


def seed_sample_material_lots():
    """Insert demo material lots in various statuses."""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) as c FROM material_lots").fetchone()["c"]
    if count > 0:
        conn.close()
        return

    lots = [
        ("API", "Paracetamol BP (Micronised)", "API-PAR-2026-001", "Aarti Drugs Ltd.",
         "2026-03-01", "2028-03-01", 500.0, "kg", "Released", "Maimouna Diabi"),
        ("Excipient", "Microcrystalline Cellulose PH102", "EXC-MCC-2026-015", "JRS Pharma",
         "2026-03-05", "2028-06-01", 200.0, "kg", "Released", "Maimouna Diabi"),
        ("Excipient", "Sucrose (Pharmaceutical Grade)", "EXC-SUC-2026-008", "Sudzucker AG",
         "2026-03-10", "2027-12-01", 300.0, "kg", "Released", "Maimouna Diabi"),
        ("Packaging", "PVC Blister Foil 250um", "PKG-BLF-2026-042", "Bilcare Ltd.",
         "2026-03-15", "2028-03-15", 50.0, "rolls", "Quarantine", None),
        ("API", "Paracetamol BP (Micronised)", "API-PAR-2026-002", "Granules India Ltd.",
         "2026-04-01", "2028-04-01", 500.0, "kg", "Quarantine", None),
        ("Packaging", "Amber Glass Bottle 100mL", "PKG-AGB-2026-018", "Gerresheimer AG",
         "2026-03-20", "2029-03-20", 10000.0, "units", "Released", "Maimouna Diabi"),
    ]

    for lot in lots:
        conn.execute(
            """INSERT INTO material_lots
               (material_type, material_name, lot_number, supplier,
                received_date, expiry_date, quantity, unit, status, released_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            lot,
        )
    conn.commit()
    conn.close()


def seed_sample_batches():
    """Insert demo production batches at various lifecycle stages."""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) as c FROM batches").fetchone()["c"]
    if count > 0:
        conn.close()
        return

    tablet = conn.execute("SELECT id FROM products WHERE product_name = ?",
                          ("Paracetamol Tablet 500 mg",)).fetchone()
    syrup = conn.execute("SELECT id FROM products WHERE product_name = ?",
                         ("Paracetamol Syrup 120 mg/5 mL",)).fetchone()

    if not tablet or not syrup:
        conn.close()
        return

    # Get stage IDs
    stages = conn.execute("SELECT id, stage_code FROM production_stages").fetchall()
    sid = {s['stage_code']: s['id'] for s in stages}

    # Batch 1: Tablet — Released (all stages passed)
    conn.execute(
        "INSERT INTO batches (batch_number, product_id, batch_size, status, current_stage_id, created_by) VALUES (?, ?, ?, ?, ?, ?)",
        ("PARA-T-20260401-001", tablet['id'], 100000, "Released", sid['FP-TAB-500'], "Maimouna Diabi"),
    )
    batch1_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    for code in ['RM-001', 'RM-002', 'PM-001', 'IPQC-T-01', 'IPQC-T-02', 'IPQC-T-03', 'FP-TAB-500']:
        conn.execute(
            "INSERT INTO batch_stage_results (batch_id, stage_id, verdict, signed_by, signed_at) VALUES (?, ?, 'PASS', 'Maimouna Diabi', CURRENT_TIMESTAMP)",
            (batch1_id, sid[code]),
        )

    # Batch 2: Tablet — In-Progress at Compression (IQC + Granulation done)
    conn.execute(
        "INSERT INTO batches (batch_number, product_id, batch_size, status, current_stage_id, created_by) VALUES (?, ?, ?, ?, ?, ?)",
        ("PARA-T-20260415-002", tablet['id'], 100000, "In-Progress", sid['IPQC-T-02'], "Maimouna Diabi"),
    )
    batch2_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    for code in ['RM-001', 'RM-002', 'PM-001', 'IPQC-T-01']:
        conn.execute(
            "INSERT INTO batch_stage_results (batch_id, stage_id, verdict, signed_by, signed_at) VALUES (?, ?, 'PASS', 'Maimouna Diabi', CURRENT_TIMESTAMP)",
            (batch2_id, sid[code]),
        )
    conn.execute(
        "INSERT INTO batch_stage_results (batch_id, stage_id, verdict, signed_by) VALUES (?, ?, 'IN_PROGRESS', 'Maimouna Diabi')",
        (batch2_id, sid['IPQC-T-02']),
    )

    # Batch 3: Syrup — Created (just created, no stages started)
    conn.execute(
        "INSERT INTO batches (batch_number, product_id, batch_size, status, created_by) VALUES (?, ?, ?, ?, ?)",
        ("PARA-S-20260416-001", syrup['id'], 5000, "Created", "Executive Viewer"),
    )

    # Link materials to batch 1 and batch 2
    conn.execute(
        "INSERT INTO batch_materials (batch_id, material_lot_id, quantity_used, unit) VALUES (?, ?, ?, ?)",
        (batch1_id, 1, 50.0, "kg"),  # API lot
    )
    conn.execute(
        "INSERT INTO batch_materials (batch_id, material_lot_id, quantity_used, unit) VALUES (?, ?, ?, ?)",
        (batch1_id, 2, 30.0, "kg"),  # MCC lot
    )
    conn.execute(
        "INSERT INTO batch_materials (batch_id, material_lot_id, quantity_used, unit) VALUES (?, ?, ?, ?)",
        (batch2_id, 1, 50.0, "kg"),  # API lot
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
    # New stage-based seeds
    seed_production_stages()
    seed_stage_checkpoints()
    seed_sample_material_lots()
    seed_sample_batches()


if __name__ == "__main__":
    from db_manager import init_db
    init_db()
    run_all_seeds()
    print("Database seeded successfully.")
