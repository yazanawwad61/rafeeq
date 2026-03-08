import sqlite3

conn = sqlite3.connect('roommate.db')
cursor = conn.cursor()

# Users table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        gender TEXT NOT NULL,
        phone TEXT,
        profile_pic TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Listings table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS listings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        apartment_type TEXT NOT NULL,
        gender_preference TEXT NOT NULL,
        rent INTEGER NOT NULL,
        area TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        rooms INTEGER,
        status TEXT DEFAULT 'pending',
        id_photo TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

# Tags table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS listing_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_id INTEGER NOT NULL,
        tag TEXT NOT NULL,
        FOREIGN KEY (listing_id) REFERENCES listings(id)
    )
''')

# Listing photos table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS listing_photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_id INTEGER NOT NULL,
        photo_path TEXT NOT NULL,
        FOREIGN KEY (listing_id) REFERENCES listings(id)
    )
''')

# Messages table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        listing_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES users(id),
        FOREIGN KEY (receiver_id) REFERENCES users(id),
        FOREIGN KEY (listing_id) REFERENCES listings(id)
    )
''')

# Admin table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
''')

conn.commit()
conn.close()

print("Done! RoommateIQ database created successfully.")
