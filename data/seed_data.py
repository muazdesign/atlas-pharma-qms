"""
Atlas Pharma QMS — Seed Data
Pre-populates the database with default users, product specs, and lab partners.
Run once after DB initialization.
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from db_manager import create_user, get_connection


def seed_users():
    """Create default user accounts."""
    create_user("admin", "atlas2026", "Admin User", "Admin")
    create_user("maimouna", "atlas2026", "Maimouna Diabi", "Quality Manager")
    create_user("busra", "atlas2026", "Büşra", "Quality Manager")
    create_user("executive", "atlas2026", "Executive Viewer", "Executive")


def seed_specs():
    """Insert Paracetamol Tablet and Syrup specifications."""
    conn = get_connection()
    # Check if already seeded
    count = conn.execute("SELECT COUNT(*) as c FROM specs_master").fetchone()["c"]
    if count > 0:
        conn.close()
        return

    specs = [
        # Paracetamol Tablet 500 mg
        ("Paracetamol Tablet 500 mg", "Tablet", "Appearance", "White to off-white, round, biconvex tablet", "Visual inspection"),
        ("Paracetamol Tablet 500 mg", "Tablet", "Average Weight", "550 ± 5% mg", "USP <791> Weight Variation"),
        ("Paracetamol Tablet 500 mg", "Tablet", "Hardness", "5 – 10 kp", "Tablet hardness tester"),
        ("Paracetamol Tablet 500 mg", "Tablet", "Friability", "≤ 1.0%", "USP <1216> Friability"),
        ("Paracetamol Tablet 500 mg", "Tablet", "Disintegration Time", "≤ 15 minutes", "USP <701> Disintegration"),
        ("Paracetamol Tablet 500 mg", "Tablet", "Assay (Paracetamol)", "95.0 – 105.0% of label claim", "HPLC (USP Monograph)"),
        ("Paracetamol Tablet 500 mg", "Tablet", "Dissolution", "≥ 80% in 30 min", "USP <711> Dissolution Apparatus II"),
        ("Paracetamol Tablet 500 mg", "Tablet", "Moisture Content", "≤ 3.0%", "Karl Fischer titration"),
        ("Paracetamol Tablet 500 mg", "Tablet", "Microbial Limits", "TAMC ≤ 10³ CFU/g, TYMC ≤ 10² CFU/g", "USP <61>/<62>"),
        # Paracetamol Syrup 120 mg/5 mL
        ("Paracetamol Syrup 120 mg/5 mL", "Syrup", "Appearance", "Clear, colorless to pale-yellow liquid, cherry-flavored", "Visual / Organoleptic"),
        ("Paracetamol Syrup 120 mg/5 mL", "Syrup", "pH", "4.5 – 6.5", "pH meter (USP <791>)"),
        ("Paracetamol Syrup 120 mg/5 mL", "Syrup", "Specific Gravity", "1.10 – 1.25 g/mL", "Densitometer"),
        ("Paracetamol Syrup 120 mg/5 mL", "Syrup", "Assay (Paracetamol)", "90.0 – 110.0% of label claim", "HPLC (USP Monograph)"),
        ("Paracetamol Syrup 120 mg/5 mL", "Syrup", "Volume per Container", "100 mL ± 2%", "Graduated cylinder"),
        ("Paracetamol Syrup 120 mg/5 mL", "Syrup", "Preservative Content", "Within approved limits", "HPLC"),
        ("Paracetamol Syrup 120 mg/5 mL", "Syrup", "Microbial Limits", "TAMC ≤ 10² CFU/mL, TYMC ≤ 10¹ CFU/mL, No E. coli", "USP <61>/<62>"),
        ("Paracetamol Syrup 120 mg/5 mL", "Syrup", "Viscosity", "50 – 200 cP", "Brookfield viscometer"),
    ]

    conn.executemany(
        "INSERT INTO specs_master (product_name, form, parameter, specification, test_method) VALUES (?, ?, ?, ?, ?)",
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

    reviews = [
        ("BTX-2026-0417", "Paracetamol Tablet 500 mg",
         "Found discoloration on tablets from this batch. Some pills have yellowish spots on the surface.",
         "Major", "Negative", "Open"),
        ("BSY-2026-0312", "Paracetamol Syrup 120 mg/5 mL",
         "The syrup has an unusual bitter aftertaste that is different from previous batches.",
         "Minor", "Negative", "Open"),
        ("BTX-2026-0390", "Paracetamol Tablet 500 mg",
         "Several tablets in the blister pack were crumbled/broken upon opening. Packaging integrity issue.",
         "Critical", "Negative", "Open"),
        ("BSY-2026-0288", "Paracetamol Syrup 120 mg/5 mL",
         "Product consistency seems thinner than usual. Pours faster than the older batch we had.",
         "Minor", "Negative", "Claimed"),
        ("BTX-2026-0401", "Paracetamol Tablet 500 mg",
         "Excellent batch quality. Tablets are well-formed and dissolve properly in water tests.",
         "Minor", "Positive", "Resolved"),
    ]

    for r in reviews:
        conn.execute(
            """INSERT INTO reviews (batch_number, product_type, review_text, ai_category, ai_sentiment, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            r,
        )
    conn.commit()
    conn.close()


def run_all_seeds():
    """Execute all seed functions."""
    seed_users()
    seed_specs()
    seed_partners()
    seed_sample_reviews()


if __name__ == "__main__":
    from db_manager import init_db
    init_db()
    run_all_seeds()
    print("✅ Database seeded successfully.")
