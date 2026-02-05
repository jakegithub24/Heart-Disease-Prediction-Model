# init_db.py
import sqlite3
import os
from werkzeug.security import generate_password_hash


def init_database():
    """Initialize the SQLite database with tables"""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, 'heart_care.db')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create users table (admin and hospital staff)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT UNIQUE,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'staff')),
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    ''')

    # Create patients table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
        contact_number TEXT,
        email TEXT,
        address TEXT,
        
        -- Heart disease parameters
        cp INTEGER,  -- chest pain type
        trestbps INTEGER,  -- resting blood pressure
        chol INTEGER,  -- cholesterol
        fbs INTEGER,  -- fasting blood sugar
        restecg INTEGER,  -- resting electrocardiographic results
        thalach INTEGER,  -- maximum heart rate achieved
        exang INTEGER,  -- exercise induced angina
        oldpeak REAL,  -- ST depression induced by exercise
        slope INTEGER,  -- slope of the peak exercise ST segment
        ca INTEGER,  -- number of major vessels colored by fluoroscopy
        thal INTEGER,  -- thalassemia
        
        -- Prediction results
        prediction_result INTEGER,  -- 0 or 1
        prediction_probability REAL,
        prediction_notes TEXT,
        
        -- Metadata
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users(id)
    )
    ''')

    # Create audit log table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        table_name TEXT NOT NULL,
        record_id INTEGER,
        old_values TEXT,
        new_values TEXT,
        ip_address TEXT,
        user_agent TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # Create indexes
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_patients_patient_id ON patients(patient_id)')
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_patients_created_by ON patients(created_by)')
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')

    # Create default admin user if not exists
    admin_password = generate_password_hash('admin123')
    cursor.execute('''
    INSERT OR IGNORE INTO users (username, password_hash, full_name, email, role)
    VALUES (?, ?, ?, ?, ?)
    ''', ('admin', admin_password, 'System Administrator', 'admin@heartcare.ai', 'admin'))

    # Create sample staff user
    staff_password = generate_password_hash('staff123')
    cursor.execute('''
    INSERT OR IGNORE INTO users (username, password_hash, full_name, email, role)
    VALUES (?, ?, ?, ?, ?)
    ''', ('staff1', staff_password, 'John Doctor', 'staff1@heartcare.ai', 'staff'))

    conn.commit()
    conn.close()
    print("Database initialized successfully!")


if __name__ == '__main__':
    init_database()
