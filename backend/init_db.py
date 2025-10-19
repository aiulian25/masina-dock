from app import app
from models import db, User
import os
import sqlite3

def migrate_database():
    db_path = '/app/data/masina_dock.db'
    
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("PRAGMA table_info(user)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'language' not in columns:
                print("Adding language column...")
                cursor.execute("ALTER TABLE user ADD COLUMN language VARCHAR(5) DEFAULT 'en'")
            
            if 'unit_system' not in columns:
                print("Adding unit_system column...")
                cursor.execute("ALTER TABLE user ADD COLUMN unit_system VARCHAR(20) DEFAULT 'imperial'")
            
            if 'currency' not in columns:
                print("Adding currency column...")
                cursor.execute("ALTER TABLE user ADD COLUMN currency VARCHAR(10) DEFAULT 'GBP'")
            
            if 'photo' not in columns:
                print("Adding photo column...")
                cursor.execute("ALTER TABLE user ADD COLUMN photo VARCHAR(255)")
            
            if 'must_change_credentials' not in columns:
                print("Adding must_change_credentials column...")
                cursor.execute("ALTER TABLE user ADD COLUMN must_change_credentials BOOLEAN DEFAULT 0")
            
            if 'email_verified' not in columns:
                print("Adding email_verified column...")
                cursor.execute("ALTER TABLE user ADD COLUMN email_verified BOOLEAN DEFAULT 1")
            
            if 'email_verification_token' not in columns:
                print("Adding email_verification_token column...")
                cursor.execute("ALTER TABLE user ADD COLUMN email_verification_token VARCHAR(100)")
            
            if 'email_verification_sent_at' not in columns:
                print("Adding email_verification_sent_at column...")
                cursor.execute("ALTER TABLE user ADD COLUMN email_verification_sent_at DATETIME")
            
            if 'two_factor_enabled' not in columns:
                print("Adding two_factor_enabled column...")
                cursor.execute("ALTER TABLE user ADD COLUMN two_factor_enabled BOOLEAN DEFAULT 0")
            
            if 'two_factor_secret' not in columns:
                print("Adding two_factor_secret column...")
                cursor.execute("ALTER TABLE user ADD COLUMN two_factor_secret VARCHAR(32)")
            
            if 'backup_codes' not in columns:
                print("Adding backup_codes column...")
                cursor.execute("ALTER TABLE user ADD COLUMN backup_codes TEXT")
            
            if 'last_login' not in columns:
                print("Adding last_login column...")
                cursor.execute("ALTER TABLE user ADD COLUMN last_login DATETIME")
            
            conn.commit()
            print("Database migration completed!")
            
        except Exception as e:
            print(f"Migration error: {e}")
            conn.rollback()
        finally:
            conn.close()

def init_database():
    with app.app_context():
        migrate_database()
        db.create_all()
        print("Database initialized successfully!")
        print("Please register your admin account at http://localhost:5000/register")

if __name__ == '__main__':
    init_database()
