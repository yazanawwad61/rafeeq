"""
seed.py — Run this ONCE to insert 40 fake listings into Rafeeq.
Usage:
  Local:      python seed.py
  Production: Set DATABASE_URL env var, then python seed.py
"""

import os, random, sqlite3

DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    import psycopg2
    conn = psycopg2.connect(DATABASE_URL)
    PLACEHOLDER = '%s'
else:
    conn = sqlite3.connect('roommate.db')
    PLACEHOLDER = '?'

cursor = conn.cursor()

# ── DATA ──────────────────────────────────────────────────────
AREAS = [
    ("Sweifieh",                31.9636, 35.8797),
    ("Abdoun",                  31.9561, 35.8697),
    ("Shmeisani",               31.9774, 35.8997),
    ("Jubeiha",                 32.0264, 35.8717),
    ("Tla Al Ali",              31.9997, 35.8697),
    ("Khalda",                  31.9797, 35.8597),
    ("Gardens",                 31.9897, 35.8997),
    ("University of Jordan Area", 32.0097, 35.8897),
    ("Mecca St",                31.9497, 35.8997),
    ("Downtown",                31.9522, 35.9333),
]

TITLES = [
    "Cozy Room in Shared Apartment",
    "Spacious Studio Near University",
    "Modern Apartment with Balcony",
    "Fully Furnished Room Available",
    "Quiet Room in Clean Flat",
    "Private Room in 3-Bedroom Apt",
    "Bright Room with Great View",
    "Room in Mixed-Use Building",
    "Central Location, Move-In Ready",
    "Near Bus Stop, All Bills Included",
    "Newly Renovated Private Room",
    "Large Room with Natural Light",
    "Affordable Room in Quiet Area",
    "Students Welcome - Near UJ",
    "Professional Area, Ideal for Students",
    "Walking Distance to Shopping",
    "Furnished Apartment, Short Stay OK",
    "Ground Floor, Private Entrance",
    "Top Floor with City View",
    "Near Medical Facilities & Uni",
]

DESCRIPTIONS = [
    "A clean and comfortable room in a well-maintained apartment. All utilities included. Quiet building with 24/7 security.",
    "Spacious room with built-in wardrobe. Shared kitchen and bathrooms. Close to main bus routes and supermarkets.",
    "Fully furnished room with high-speed WiFi. Air conditioning in all rooms. Great for students and professionals.",
    "Peaceful environment, ideal for studying. Clean shared kitchen. Bills included in rent. Available immediately.",
    "Modern apartment in a prime location. Parking available. Close to restaurants, cafes, and public transport.",
    "Comfortable room in a friendly household. Kitchen access fully included. Ideal for students or young professionals.",
    "Recently renovated apartment. High ceilings and large windows. Great natural light throughout the day.",
    "Room available in a 3-bedroom apartment. Two flatmates already in place. Clean, respectful atmosphere.",
]

TAGS_POOL = [
    ["Doesn't Smoke", "Quiet Lifestyle"],
    ["Prays", "Doesn't Smoke"],
    ["Students Only", "Quiet Lifestyle"],
    ["Doesn't Bring Guests", "Doesn't Smoke"],
    ["Pet Friendly"],
    ["Prays", "Students Only", "Quiet Lifestyle"],
    ["Doesn't Smoke", "Students Only"],
    [],
    ["Quiet Lifestyle"],
    ["Doesn't Bring Guests"],
]

# Real apartment photos from Unsplash (free to use)
PHOTOS = [
    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800&q=80",
    "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800&q=80",
    "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800&q=80",
    "https://images.unsplash.com/photo-1484154218962-a197022b5858?w=800&q=80",
    "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=800&q=80",
    "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=800&q=80",
    "https://images.unsplash.com/photo-1536376072261-38c75010e6c9?w=800&q=80",
    "https://images.unsplash.com/photo-1507089947368-19c1da9775ae?w=800&q=80",
    "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800&q=80",
    "https://images.unsplash.com/photo-1574362848149-11496d93a7c7?w=800&q=80",
]

GENDERS    = ["male", "female", "any", "male", "female", "any", "male", "female"]
APT_TYPES  = ["shared", "shared", "private", "shared", "private", "shared"]

# ── GET SEED USER ID ──────────────────────────────────────────
p = PLACEHOLDER
cursor.execute(f"SELECT id FROM users LIMIT 1")
row = cursor.fetchone()
if not row:
    print("No users found. Please create an account first, then run this script.")
    conn.close()
    exit()

user_id = row[0]
print(f"Using user_id: {user_id}")

# ── INSERT 40 LISTINGS ────────────────────────────────────────
inserted = 0
for i in range(40):
    area_name, base_lat, base_lng = random.choice(AREAS)
    lat = base_lat + random.uniform(-0.008, 0.008)
    lng = base_lng + random.uniform(-0.008, 0.008)

    title   = random.choice(TITLES)
    desc    = random.choice(DESCRIPTIONS)
    gender  = random.choice(GENDERS)
    apt_type = random.choice(APT_TYPES)
    rent    = random.choice([100, 120, 130, 150, 160, 180, 200, 220, 250, 280, 300])
    rooms   = random.randint(1, 4)
    tags    = random.choice(TAGS_POOL)
    photo   = PHOTOS[i % len(PHOTOS)]

    # Insert listing (approved immediately for seed data)
    if DATABASE_URL:
        cursor.execute(f"""
            INSERT INTO listings (user_id, title, description, apartment_type, gender_preference,
                rent, area, rooms, latitude, longitude, status)
            VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},'approved')
            RETURNING id
        """, (user_id, title, desc, apt_type, gender, rent, area_name, rooms, lat, lng))
        listing_id = cursor.fetchone()[0]
    else:
        cursor.execute(f"""
            INSERT INTO listings (user_id, title, description, apartment_type, gender_preference,
                rent, area, rooms, latitude, longitude, status)
            VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},'approved')
        """, (user_id, title, desc, apt_type, gender, rent, area_name, rooms, lat, lng))
        listing_id = cursor.lastrowid

    # Insert photo (using Unsplash URL directly)
    cursor.execute(f"INSERT INTO listing_photos (listing_id, photo_path) VALUES ({p},{p})", (listing_id, photo))

    # Insert tags
    for tag in tags:
        cursor.execute(f"INSERT INTO listing_tags (listing_id, tag) VALUES ({p},{p})", (listing_id, tag))

    inserted += 1
    print(f"  [{inserted}/40] Inserted: {title} — {area_name} — {rent} JD — {gender}")

conn.commit()
conn.close()
print(f"\nDone! {inserted} listings inserted successfully.")