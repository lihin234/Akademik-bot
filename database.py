import sqlite3

DB_NAME = "chat_memory.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            content TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_memory(user_id, role, content):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (user_id, role, content)
        VALUES (?, ?, ?)
    ''', (user_id, role, content))
    conn.commit()
    conn.close()

def get_memory(user_id, limit=8):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # SQL FIX: Menambahkan kolom 'id' di inner-select agar bisa diurutkan oleh outer-select
    cursor.execute('''
        SELECT role, content FROM (
            SELECT id, role, content FROM messages
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        ) ORDER BY id ASC
    ''', (user_id, limit))
    rows = cursor.fetchall()
    conn.close()

    messages =[]
    for role, content in rows:
        messages.append({
            "role": role,
            "content": [{"text": content}]
        })
    return messages

def clear_memory(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM messages WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
