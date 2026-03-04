import sqlite3
import os

DATABASE_URL = 'database.db'

def create_database(DATABASE_URL):
    print(os.path.abspath(DATABASE_URL))
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                
        )
    ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            price REAL NOT NULL,
            category TEXT,
            stock_quantity INTEGER NOT NULL DEFAULT 0,
            tax REAL,
            expiry_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sellers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                business_name TEXT NOT NULL,
                gst_number TEXT NOT NULL UNIQUE,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                verified BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
    
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer_orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now'))
                )
            ''')
        conn.commit()
        conn.close()
        print("Database created successfully")
    except sqlite3.Error as e:
        print(f"Error: {e}")
