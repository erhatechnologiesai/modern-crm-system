import sqlite3
import hashlib
import os
from contextlib import contextmanager
from app.config import settings

def get_db_path():
    return os.environ.get("DATABASE_PATH", settings.db_path)

@contextmanager
def get_db():
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def hash_password(password: str) -> str:
    salt = "crm_salt_2026"
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Users Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            hashed_password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'sales_rep',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Companies Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            industry TEXT,
            website TEXT,
            size TEXT,
            annual_revenue REAL DEFAULT 0,
            city TEXT,
            country TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Contacts Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            title TEXT,
            status TEXT DEFAULT 'lead',
            lead_source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Leads Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
            company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL,
            value REAL DEFAULT 0,
            status TEXT DEFAULT 'new',
            source TEXT,
            notes TEXT,
            assigned_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Deals Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL,
            contact_id INTEGER REFERENCES contacts(id) ON DELETE SET NULL,
            amount REAL NOT NULL DEFAULT 0,
            stage TEXT NOT NULL DEFAULT 'prospect',
            probability INTEGER DEFAULT 20,
            expected_close_date TEXT,
            assigned_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Tasks Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            due_date TEXT,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            related_entity_type TEXT,
            related_entity_id INTEGER,
            assigned_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Notes Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            author_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Activity Logs Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Seed Admin User if none exists
        cursor.execute("SELECT id FROM users WHERE email = 'admin@apexcrm.io'")
        if not cursor.fetchone():
            cursor.execute("""
            INSERT INTO users (email, full_name, hashed_password, role, is_active)
            VALUES (?, ?, ?, ?, 1)
            """, ('admin@apexcrm.io', 'Sarah Connor (Admin)', hash_password('Admin@Apex2026!'), 'admin'))
            admin_id = cursor.lastrowid

            cursor.execute("""
            INSERT INTO users (email, full_name, hashed_password, role, is_active)
            VALUES (?, ?, ?, ?, 1)
            """, ('manager@apexcrm.io', 'Marcus Vance (Manager)', hash_password('Manager@Apex2026!'), 'sales_manager'))
            
            cursor.execute("""
            INSERT INTO users (email, full_name, hashed_password, role, is_active)
            VALUES (?, ?, ?, ?, 1)
            """, ('rep@apexcrm.io', 'Elena Rostova (Rep)', hash_password('Rep@Apex2026!'), 'sales_rep'))

            # Seed Companies
            cursor.execute("""
            INSERT INTO companies (name, industry, website, size, annual_revenue, city, country)
            VALUES 
            ('CloudScale Systems', 'Enterprise Software', 'https://cloudscale.example.com', '250-500', 45000000, 'San Francisco', 'USA'),
            ('BioHealth Labs', 'Healthcare & Biotech', 'https://biohealth.example.com', '50-100', 12000000, 'Boston', 'USA'),
            ('Apex Logistics Corp', 'Supply Chain', 'https://apexlogistics.example.com', '1000+', 180000000, 'Chicago', 'USA'),
            ('FinVantage Analytics', 'Financial Services', 'https://finvantage.example.com', '100-250', 28000000, 'New York', 'USA')
            """)

            # Seed Contacts
            cursor.execute("""
            INSERT INTO contacts (company_id, first_name, last_name, email, phone, title, status, lead_source)
            VALUES 
            (1, 'David', 'Miller', 'david.m@cloudscale.example.com', '+1-415-555-0142', 'Chief Technology Officer', 'customer', 'Referral'),
            (1, 'Jessica', 'Alba', 'jessica.a@cloudscale.example.com', '+1-415-555-0199', 'VP Engineering', 'customer', 'Conference'),
            (2, 'Dr. Robert', 'Chen', 'rchen@biohealth.example.com', '+1-617-555-0811', 'Head of Clinical Research', 'active', 'Inbound Web'),
            (3, 'Samantha', 'Fox', 's.fox@apexlogistics.example.com', '+1-312-555-0374', 'Procurement Director', 'lead', 'Outbound Sales'),
            (4, 'Michael', 'Sterling', 'msterling@finvantage.example.com', '+1-212-555-0722', 'Chief Operating Officer', 'customer', 'LinkedIn')
            """)

            # Seed Leads
            cursor.execute("""
            INSERT INTO leads (title, contact_id, company_id, value, status, source, notes, assigned_user_id)
            VALUES 
            ('Multi-region Cloud Security Upgrade', 1, 1, 75000, 'qualified', 'Referral', 'Looking to deploy Q3 across 4 global regions.', ?),
            ('Genomics Workflow Orchestration Suite', 3, 2, 120000, 'contacted', 'Inbound Web', 'Needs SOC2 and HIPAA compliant integration.', ?),
            ('Fleet Telematics Fleet Integration', 4, 3, 210000, 'new', 'Outbound Sales', 'Inquiry regarding 1200 truck sensors.', ?)
            """, (admin_id, admin_id, admin_id))

            # Seed Deals
            cursor.execute("""
            INSERT INTO deals (title, company_id, contact_id, amount, stage, probability, expected_close_date, assigned_user_id)
            VALUES 
            ('CloudScale Enterprise Tier Expansion', 1, 1, 145000, 'negotiation', 80, '2026-11-15', ?),
            ('BioHealth Data Lake License', 2, 3, 98000, 'proposal', 60, '2026-10-30', ?),
            ('Apex Logistics Fleet Gateway Phase 1', 3, 4, 320000, 'closed_won', 100, '2026-09-01', ?),
            ('FinVantage Real-time Fraud Engine', 4, 5, 250000, 'qualification', 40, '2026-12-20', ?)
            """, (admin_id, admin_id, admin_id, admin_id))

            # Seed Tasks
            cursor.execute("""
            INSERT INTO tasks (title, description, due_date, priority, status, related_entity_type, related_entity_id, assigned_user_id)
            VALUES 
            ('Finalize Master Services Agreement for CloudScale', 'Review terms with legal team prior to contract execution.', '2026-10-05', 'urgent', 'in_progress', 'deal', 1, ?),
            ('Schedule Technical Architecture Review with BioHealth', 'Deep dive with Dr. Chen on HIPAA audit controls.', '2026-10-08', 'high', 'pending', 'deal', 2, ?),
            ('Send Onboarding Guide to Apex Logistics', 'Deliver credentials and API gateway handbook.', '2026-09-28', 'medium', 'completed', 'company', 3, ?)
            """, (admin_id, admin_id, admin_id))

            # Seed Activity Logs
            cursor.execute("""
            INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details)
            VALUES 
            (?, 'SYSTEM_INIT', 'system', 0, 'Database initialized with enterprise baseline dataset.'),
            (?, 'DEAL_WON', 'deal', 3, 'Apex Logistics Fleet Gateway marked closed_won for $320,000.'),
            (?, 'STAGE_CHANGE', 'deal', 1, 'CloudScale deal moved to negotiation (80% probability).')
            """, (admin_id, admin_id, admin_id))
