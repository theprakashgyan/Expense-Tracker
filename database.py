import sqlite3
import bcrypt
import os

DB_PATH = 'expense_tracker.db'

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    # Create family_members table
    c.execute('''
        CREATE TABLE IF NOT EXISTS family_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            earning_status BOOLEAN NOT NULL,
            earnings REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    # Create expenses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            value REAL NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    
    # Auto-seed the admin account with default password if it doesn't exist
    try:
        admin_pass = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', ('admin', admin_pass))
        conn.commit()
    except sqlite3.IntegrityError:
        pass # Admin already exists

    conn.close()

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                  (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
    row = c.fetchone()
    conn.close()
    
    if row and verify_password(password, row[1]):
        return {"id": row[0], "username": username}
    return None

def get_all_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, username FROM users')
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_members():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT fm.id, u.username, fm.name, fm.earning_status, fm.earnings 
        FROM family_members fm 
        JOIN users u ON fm.user_id = u.id
    ''')
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_expenses():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT e.id, u.username, e.category, e.description, e.value, e.date 
        FROM expenses e 
        JOIN users u ON e.user_id = u.id
    ''')
    rows = c.fetchall()
    conn.close()
    return rows

# Ensure db structure exists on load
if not os.path.exists(DB_PATH):
    init_db()
else:
    init_db()
