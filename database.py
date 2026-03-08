import sqlite3

conn = sqlite3.connect('roommate.db')
cursor = conn.cursor()

# ── USERS ──────────────────────────────────────────────────────────
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    gender TEXT NOT NULL CHECK(gender IN ('male', 'female')),
    phone TEXT,
    profile_pic TEXT,
    is_verified INTEGER DEFAULT 0,
    verify_token TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# ── LISTINGS ───────────────────────────────────────────────────────
cursor.execute('''
CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    apartment_type TEXT NOT NULL CHECK(apartment_type IN ('shared', 'private')),
    gender_preference TEXT NOT NULL CHECK(gender_preference IN ('male', 'female', 'any')),
    rent REAL NOT NULL,
    area TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    rooms INTEGER,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
    id_photo TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')

# ── LISTING TAGS ───────────────────────────────────────────────────
cursor.execute('''
CREATE TABLE IF NOT EXISTS listing_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    tag TEXT NOT NULL,
    FOREIGN KEY (listing_id) REFERENCES listings(id)
)
''')

# ── LISTING PHOTOS ─────────────────────────────────────────────────
cursor.execute('''
CREATE TABLE IF NOT EXISTS listing_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    photo_path TEXT NOT NULL,
    FOREIGN KEY (listing_id) REFERENCES listings(id)
)
''')

# ── MESSAGES ───────────────────────────────────────────────────────
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

# ── ADMINS ─────────────────────────────────────────────────────────
cursor.execute('''
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
''')

# ── REPORTS ────────────────────────────────────────────────────────
cursor.execute('''
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reporter_id INTEGER NOT NULL,
    listing_id INTEGER NOT NULL,
    reason TEXT NOT NULL CHECK(reason IN ('fake', 'harassment', 'discrimination', 'other')),
    description TEXT,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'reviewed', 'resolved')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reporter_id) REFERENCES users(id),
    FOREIGN KEY (listing_id) REFERENCES listings(id)
)
''')

# ── RATINGS ────────────────────────────────────────────────────────
cursor.execute('''
CREATE TABLE IF NOT EXISTS ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rater_id INTEGER NOT NULL,
    rated_user_id INTEGER NOT NULL,
    listing_id INTEGER NOT NULL,
    accuracy INTEGER CHECK(accuracy BETWEEN 1 AND 5),
    communication INTEGER CHECK(communication BETWEEN 1 AND 5),
    reliability INTEGER CHECK(reliability BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rater_id) REFERENCES users(id),
    FOREIGN KEY (rated_user_id) REFERENCES users(id),
    FOREIGN KEY (listing_id) REFERENCES listings(id)
)
''')

# ── INDEXES (performance on common filters) ────────────────────────
cursor.execute(
    'CREATE INDEX IF NOT EXISTS idx_listings_status ON listings(status)')
cursor.execute(
    'CREATE INDEX IF NOT EXISTS idx_listings_gender ON listings(gender_preference)')
cursor.execute(
    'CREATE INDEX IF NOT EXISTS idx_listings_rent ON listings(rent)')
cursor.execute(
    'CREATE INDEX IF NOT EXISTS idx_listings_area ON listings(area)')
cursor.execute(
    'CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id)')
cursor.execute(
    'CREATE INDEX IF NOT EXISTS idx_messages_receiver ON messages(receiver_id)')
cursor.execute(
    'CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status)')

conn.commit()
conn.close()

print("Database updated successfully.")
print("Tables: users, listings, listing_tags, listing_photos, messages, admins, reports, ratings")
print("Indexes: status, gender, rent, area, messages, reports")
