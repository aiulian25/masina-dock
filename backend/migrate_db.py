import sqlite3
import os

def migrate_database():
    db_path = '/app/data/masina_dock.db'
    
    if not os.path.exists(db_path):
        print("Database does not exist. Will be created on first run.")
        return
    
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
            cursor.execute("ALTER TABLE user ADD COLUMN unit_system VARCHAR(20) DEFAULT 'metric'")
        
        if 'currency' not in columns:
            print("Adding currency column...")
            cursor.execute("ALTER TABLE user ADD COLUMN currency VARCHAR(10) DEFAULT 'USD'")
        
        conn.commit()
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Migration error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
