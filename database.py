import sqlite3

def init_db():
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    # បន្ថែមជួរឈរ gender ចូលក្នុងតារាង
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            gender TEXT,
            name TEXT,
            age INTEGER,
            bio TEXT,
            photo_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id, gender, name, age, bio, photo_url):
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, gender, name, age, bio, photo_url)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, gender, name, age, bio, photo_url))
    conn.commit()
    conn.close()

def get_random_user(current_user_id, current_gender):
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    
    # កំណត់ភេទផ្ទុយគ្នា (ប្រុស រក ស្រី, ស្រី រក ប្រុស)
    target_gender = 'ស្រី 👩' if current_gender == 'ប្រុស 👨' else 'ប្រុស 👨'
    
    # ទាញយកតែអ្នកដែលមានភេទផ្ទុយគ្នាប៉ុណ្ណោះ
    cursor.execute('''
        SELECT user_id, gender, name, age, bio, photo_url FROM users 
        WHERE user_id != ? AND gender = ?
        ORDER BY RANDOM() LIMIT 1
    ''', (current_user_id, target_gender))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT gender, name, age, bio, photo_url FROM users 
        WHERE user_id = ?
    ''', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user