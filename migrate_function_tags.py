#!/usr/bin/env python3
"""
Migration script to add Function Tags tables to existing database.
Run this once to create the new tables and seed the default function categories.

Usage: python migrate_function_tags.py
"""

import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent / "scan_history.db"

def migrate():
    """Add new tables for function tags and seed data."""
    print(f"Migrating database: {DB_PATH}")

    if not DB_PATH.exists():
        print("Database not found. Run the app first to create it.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create new tables
    print("Creating function_categories table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS function_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            parent_code TEXT,
            sort_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            color TEXT DEFAULT '#3b82f6',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_code) REFERENCES function_categories(code)
        )
    ''')

    print("Creating role_function_tags table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS role_function_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER,
            role_name TEXT,
            function_code TEXT NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            assigned_by TEXT DEFAULT 'system',
            FOREIGN KEY (role_id) REFERENCES roles(id),
            FOREIGN KEY (function_code) REFERENCES function_categories(code),
            UNIQUE(role_id, function_code),
            UNIQUE(role_name, function_code)
        )
    ''')

    print("Creating document_category_types table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_category_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            doc_number_patterns TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    print("Creating document_categories table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            document_name TEXT,
            category_type TEXT NOT NULL,
            function_code TEXT,
            doc_number TEXT,
            document_owner TEXT,
            auto_detected INTEGER DEFAULT 0,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            assigned_by TEXT DEFAULT 'system',
            FOREIGN KEY (document_id) REFERENCES documents(id),
            FOREIGN KEY (function_code) REFERENCES function_categories(code)
        )
    ''')

    print("Creating role_required_actions table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS role_required_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER,
            role_name TEXT NOT NULL,
            statement_text TEXT NOT NULL,
            statement_type TEXT DEFAULT 'requirement',
            source_document_id INTEGER,
            source_document_name TEXT,
            source_location TEXT,
            confidence_score REAL DEFAULT 1.0,
            is_verified INTEGER DEFAULT 0,
            verified_by TEXT,
            verified_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (role_id) REFERENCES roles(id),
            FOREIGN KEY (source_document_id) REFERENCES documents(id)
        )
    ''')

    # Create indexes
    print("Creating indexes...")
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_role_function_tags_role
        ON role_function_tags(role_name)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_role_function_tags_function
        ON role_function_tags(function_code)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_document_categories_doc
        ON document_categories(document_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_document_categories_function
        ON document_categories(function_code)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_role_required_actions_role
        ON role_required_actions(role_name)
    ''')

    conn.commit()

    # Check if we need to seed data
    cursor.execute('SELECT COUNT(*) FROM function_categories')
    count = cursor.fetchone()[0]

    if count == 0:
        print("Seeding function categories...")
        seed_function_categories(cursor)
        seed_document_category_types(cursor)
        conn.commit()
        print(f"Seeded function categories.")
    else:
        print(f"Function categories already exist ({count} entries). Skipping seed.")

    conn.close()
    print("Migration complete!")

def seed_function_categories(cursor):
    """Seed default function categories based on organizational structure."""
    categories = [
        # Top-level functions under Org
        ('BM', 'Bus Mgmt', 'Business Management', None, 1, '#6366f1'),
        ('BD', 'Bus Dev', 'Business Development', None, 2, '#8b5cf6'),

        # Engineering and sub-functions
        ('ENG', 'Engineering', 'Engineering functions', None, 3, '#3b82f6'),
        ('AW', 'AW', 'Airworthiness', 'ENG', 4, '#60a5fa'),
        ('AVI', 'AvI', 'Avionics Integration', 'ENG', 5, '#60a5fa'),
        ('EPT', 'EP&T', 'Engineering Planning & Technology', 'ENG', 6, '#60a5fa'),

        # FS - Flight Sciences
        ('FS', 'FS', 'Flight Sciences', 'ENG', 7, '#2563eb'),
        ('FS-AERO', 'FS-Aerodynamics', 'Aerodynamics', 'FS', 8, '#3b82f6'),
        ('FS-AD', 'FS-Aircraft Dynamics', 'Aircraft Dynamics', 'FS', 9, '#3b82f6'),
        ('FS-AL', 'FS-Aircraft Loads', 'Aircraft Loads', 'FS', 10, '#3b82f6'),
        ('FS-CFD', 'FS-CFD', 'Computational Fluid Dynamics', 'FS', 11, '#3b82f6'),
        ('FS-CONFIG', 'FS-Configuration', 'Configuration', 'FS', 12, '#3b82f6'),
        ('FS-MP', 'FS-Mass Prop', 'Mass Properties', 'FS', 13, '#3b82f6'),
        ('FS-MDAO', 'FS-MDAO', 'Multidisciplinary Design Analysis & Optimization', 'FS', 14, '#3b82f6'),
        ('FS-PROP', 'FS-Propulsion', 'Propulsion', 'FS', 15, '#3b82f6'),
        ('FS-VP', 'FS-Vehicle Perf', 'Vehicle Performance', 'FS', 16, '#3b82f6'),

        # PM&P
        ('PMP', 'PM&P', 'Program Management & Planning', 'ENG', 17, '#2563eb'),

        # PS - Product Support
        ('PS', 'PS', 'Product Support', 'ENG', 18, '#2563eb'),
        ('PS-FFS', 'PS-FFS', 'Field & Fleet Support', 'PS', 19, '#3b82f6'),
        ('PS-FHR', 'PS-FHR', 'Fleet Health & Reliability', 'PS', 20, '#3b82f6'),
        ('PS-LSA', 'PS-LSA/MaPL', 'Logistics Support Analysis', 'PS', 21, '#3b82f6'),
        ('PS-MS', 'PS-M&S', 'Modeling & Simulation', 'PS', 22, '#3b82f6'),
        ('PS-OBS', 'PS-OBS Mgmt', 'Obsolescence Management', 'PS', 23, '#3b82f6'),
        ('PS-PHM', 'PS-PhM', 'Prognostics & Health Management', 'PS', 24, '#3b82f6'),
        ('PS-PSM', 'PS-PSM', 'Product Support Management', 'PS', 25, '#3b82f6'),
        ('PS-RM', 'PS-R&M', 'Reliability & Maintainability', 'PS', 26, '#3b82f6'),
        ('PS-SEE', 'PS-SEE', 'Support Equipment Engineering', 'PS', 27, '#3b82f6'),
        ('PS-SSH', 'PS-SSH', 'Spares & Supply Support', 'PS', 28, '#3b82f6'),
        ('PS-SLO', 'PS-SLO', 'Support Logistics Operations', 'PS', 29, '#3b82f6'),
        ('PS-TD', 'PS-TD', 'Technical Data', 'PS', 30, '#3b82f6'),
        ('PS-TTS', 'PS-TTS', 'Training & Training Systems', 'PS', 31, '#3b82f6'),

        # SW, SI&O, SRV
        ('SW', 'SW', 'Software', 'ENG', 32, '#2563eb'),
        ('SIO', 'SI&O', 'Systems Integration & Operations', 'ENG', 33, '#2563eb'),
        ('SRV', 'SRV', 'Survivability', 'ENG', 34, '#2563eb'),

        # SE - Systems Engineering
        ('SE', 'SE', 'Systems Engineering', 'ENG', 35, '#2563eb'),
        ('SE-CDM', 'SE-CDM', 'Configuration & Data Management', 'SE', 36, '#3b82f6'),
        ('SE-COMMS', 'SE-Comms', 'Communications', 'SE', 37, '#3b82f6'),
        ('SE-COST', 'SE-Cost Eng (LCC)', 'Cost Engineering / Life Cycle Cost', 'SE', 38, '#3b82f6'),
        ('SE-DI', 'SE-Design Int', 'Design Integration', 'SE', 39, '#3b82f6'),
        ('SE-EEE', 'SE-EEE', 'Electrical/Electronic Engineering', 'SE', 40, '#3b82f6'),
        ('SE-HSI', 'SE-Human Sys Int (HSI)', 'Human Systems Integration', 'SE', 41, '#3b82f6'),
        ('SE-IFC', 'SE-IFC', 'Interface Control', 'SE', 42, '#3b82f6'),
        ('SE-MBSE', 'SE-MBSE', 'Model-Based Systems Engineering', 'SE', 43, '#3b82f6'),
        ('SE-MES', 'SE-Mission Eng/M&S', 'Mission Engineering / M&S', 'SE', 44, '#3b82f6'),
        ('SE-NS', 'SE-Nuclear Surety', 'Nuclear Surety', 'SE', 45, '#3b82f6'),
        ('SE-RV', 'SE-Req\'ts & Verif (R&V)', 'Requirements & Verification', 'SE', 46, '#3b82f6'),
        ('SE-SEI', 'SE-SE&I', 'Systems Engineering & Integration', 'SE', 47, '#3b82f6'),
        ('SE-SS', 'SE-Sys Safety', 'System Safety', 'SE', 48, '#3b82f6'),
        ('SE-VLF', 'SE-Vuln & Live Fire', 'Vulnerability & Live Fire', 'SE', 49, '#3b82f6'),
        ('SE-HIVE', 'SE-HIVE', 'HIVE', 'SE', 50, '#3b82f6'),

        # T&E - Test & Evaluation
        ('TE', 'T&E', 'Test & Evaluation', 'ENG', 51, '#2563eb'),
        ('TE-AGILE', 'T&E-Agile', 'Agile', 'TE', 52, '#3b82f6'),
        ('TE-EAM', 'T&E-Eng Asset Mgmt (EAM)', 'Engineering Asset Management', 'TE', 53, '#3b82f6'),
        ('TE-FT', 'T&E-Flight Test', 'Flight Test', 'TE', 54, '#3b82f6'),
        ('TE-INST', 'T&E-Instrumentation', 'Instrumentation', 'TE', 55, '#3b82f6'),
        ('TE-LD', 'T&E-Lab Design', 'Lab Design', 'TE', 56, '#3b82f6'),
        ('TE-LO', 'T&E-Lab Ops', 'Lab Operations', 'TE', 57, '#3b82f6'),
        ('TE-PROC', 'T&E-Process', 'Process', 'TE', 58, '#3b82f6'),
        ('TE-SKT', 'T&E-Skills&Training', 'Skills & Training', 'TE', 59, '#3b82f6'),
        ('TE-ST', 'T&E-Specialty Test (ST)', 'Specialty Test', 'TE', 60, '#3b82f6'),
        ('TE-TLDP', 'T&E-Staffing (TLDP)', 'Staffing (TLDP)', 'TE', 61, '#3b82f6'),
        ('TE-STE', 'T&E-System Test Eng', 'System Test Engineering', 'TE', 62, '#3b82f6'),
        ('TE-TOOLS', 'T&E-Tools', 'Tools', 'TE', 63, '#3b82f6'),
        ('TE-TPR', 'T&E-TP&R', 'Test Planning & Reporting', 'TE', 64, '#3b82f6'),

        # VE - Vehicle Engineering
        ('VE', 'VE', 'Vehicle Engineering', 'ENG', 65, '#2563eb'),
        ('VE-CTRL', 'VE-Controls', 'Controls', 'VE', 66, '#3b82f6'),
        ('VE-ELEC', 'VE-Electrical', 'Electrical', 'VE', 67, '#3b82f6'),
        ('VE-FT', 'VE-Fluid/Therm', 'Fluid/Thermal', 'VE', 68, '#3b82f6'),
        ('VE-LIAS', 'VE-Liaison', 'Liaison', 'VE', 69, '#3b82f6'),
        ('VE-MECH', 'VE-Mechanical', 'Mechanical', 'VE', 70, '#3b82f6'),
        ('VE-SATMP', 'VE-SATMP', 'SATMP', 'VE', 71, '#3b82f6'),
        ('VE-STRD', 'VE-Struct Design', 'Structural Design', 'VE', 72, '#3b82f6'),
        ('VE-WEAP', 'VE-Weapons', 'Weapons', 'VE', 73, '#3b82f6'),

        # WSC
        ('WSC', 'WSC', 'Weapon System Cybersecurity', 'ENG', 74, '#2563eb'),

        # Other top-level functions
        ('HR', 'HR', 'Human Resources', None, 75, '#ec4899'),
        ('IT', 'Info Tech (IT)', 'Information Technology', None, 76, '#8b5cf6'),
        ('MA', 'Mission Assurance', 'Mission Assurance', None, 77, '#f59e0b'),
        ('NAT', 'NAT', 'NAT', None, 78, '#06b6d4'),
        ('PM', 'Prog Mgmt (PM)', 'Program Management', None, 79, '#10b981'),
        ('PROD', 'Production', 'Production', None, 80, '#22c55e'),
        ('SC', 'Supply Chain (GSC)', 'Supply Chain / Global Supply Chain', None, 81, '#14b8a6'),
        ('SEC', 'Security', 'Security', None, 82, '#ef4444'),
        ('TBD', '(TBD)', 'To Be Determined', None, 83, '#9ca3af'),

        # Facilities and sub-functions
        ('FAC', 'Facilities', 'Facilities', None, 84, '#84cc16'),
        ('FAC-PLAN', 'Facilities-Planning', 'Facilities Planning', 'FAC', 85, '#a3e635'),
        ('FAC-EST', 'Facilities-Estimating', 'Facilities Estimating', 'FAC', 86, '#a3e635'),
        ('FAC-PM', 'Facilities-Project Management', 'Facilities Project Management', 'FAC', 87, '#a3e635'),
        ('FAC-MAINT', 'Facilities-Maintenance', 'Facilities Maintenance', 'FAC', 88, '#a3e635'),
        ('FAC-OTH', 'Facilities-Other', 'Facilities Other', 'FAC', 89, '#a3e635'),

        # ESH&M, Operations, Legal
        ('ESHM', 'ESH&M', 'Environmental Safety Health & Mission Assurance', None, 90, '#eab308'),
        ('OPS', 'Operations', 'Operations', None, 91, '#f97316'),
        ('LEGAL', 'Legal', 'Legal', None, 92, '#6366f1'),
    ]

    for code, name, desc, parent, sort_order, color in categories:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO function_categories
                (code, name, description, parent_code, sort_order, color)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (code, name, desc, parent, sort_order, color))
        except Exception as e:
            print(f"Error seeding category {code}: {e}")

def seed_document_category_types(cursor):
    """Seed default document category types."""
    doc_types = [
        ('Procedures', 'Standard operating procedures and processes', 'PRO-,PROC-,P-'),
        ('Knowledgebase', 'Reference documents and knowledge articles', 'KB-,KA-,REF-'),
        ('Specifications', 'Technical specifications and standards', 'SPEC-,STD-,S-'),
        ('Instructions', 'Work instructions and guides', 'WI-,INS-,I-'),
        ('Forms', 'Standard forms and templates', 'FRM-,FORM-,F-'),
        ('Reports', 'Analysis and status reports', 'RPT-,REP-,R-'),
        ('Plans', 'Project and program plans', 'PLN-,PLAN-'),
        ('Policies', 'Corporate policies', 'POL-,POLICY-'),
    ]

    for name, desc, patterns in doc_types:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO document_category_types
                (name, description, doc_number_patterns)
                VALUES (?, ?, ?)
            ''', (name, desc, patterns))
        except Exception as e:
            print(f"Error seeding doc type {name}: {e}")


if __name__ == '__main__':
    migrate()
