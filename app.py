from flask import Flask, request, jsonify, session, render_template
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'rafeeq-secret-key-2026'


def get_db():
    conn = sqlite3.connect('roommate.db')
    conn.row_factory = sqlite3.Row
    return conn

# ─── SIGNUP ───────────────────────────────────────────


@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()

    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    gender = data.get('gender', '').strip()
    phone = data.get('phone', '').strip()

    # Validation
    if not name or not email or not password or not gender:
        return jsonify({'error': 'All fields are required'}), 400

    if gender not in ['male', 'female']:
        return jsonify({'error': 'Gender must be male or female'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    hashed_password = generate_password_hash(password)

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO users (name, email, password, gender, phone)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, email, hashed_password, gender, phone))
        conn.commit()

        user_id = cursor.lastrowid
        session['user_id'] = user_id
        session['user_name'] = name
        session['user_gender'] = gender

        return jsonify({
            'message': 'Account created successfully',
            'user': {'id': user_id, 'name': name, 'gender': gender}
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already registered'}), 409

    finally:
        conn.close()

# ─── LOGIN ────────────────────────────────────────────


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()

    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()

    if user is None:
        return jsonify({'error': 'No account found with this email'}), 404

    if not check_password_hash(user['password'], password):
        return jsonify({'error': 'Incorrect password'}), 401

    session['user_id'] = user['id']
    session['user_name'] = user['name']
    session['user_gender'] = user['gender']

    return jsonify({
        'message': 'Logged in successfully',
        'user': {'id': user['id'], 'name': user['name'], 'gender': user['gender']}
    })

# ─── LOGOUT ───────────────────────────────────────────


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

# ─── GET CURRENT USER ─────────────────────────────────


@app.route('/api/me', methods=['GET'])
def get_current_user():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    return jsonify({
        'id':     session['user_id'],
        'name':   session['user_name'],
        'gender': session['user_gender']
    })

# ─── CREATE LISTING ───────────────────────────────────


@app.route('/api/listings', methods=['POST'])
def create_listing():
    if 'user_id' not in session:
        return jsonify({'error': 'You must be logged in to post a listing'}), 401

    data = request.get_json()

    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    apartment_type = data.get('apartment_type', '').strip()
    gender_preference = data.get('gender_preference', '').strip()
    rent = data.get('rent', 0)
    area = data.get('area', '').strip()
    latitude = data.get('latitude', None)
    longitude = data.get('longitude', None)
    rooms = data.get('rooms', 1)
    tags = data.get('tags', [])

    if not title or not apartment_type or not gender_preference or not rent or not area:
        return jsonify({'error': 'Missing required fields'}), 400

    if gender_preference not in ['male', 'female', 'any']:
        return jsonify({'error': 'Gender preference must be male, female, or any'}), 400

    if apartment_type not in ['shared', 'private']:
        return jsonify({'error': 'Apartment type must be shared or private'}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO listings (user_id, title, description, apartment_type, gender_preference, rent, area, latitude, longitude, rooms, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
    ''', (session['user_id'], title, description, apartment_type, gender_preference, rent, area, latitude, longitude, rooms))

    listing_id = cursor.lastrowid

    for tag in tags:
        cursor.execute(
            'INSERT INTO listing_tags (listing_id, tag) VALUES (?, ?)', (listing_id, tag))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Listing submitted for review', 'listing_id': listing_id}), 201


# ─── GET ALL APPROVED LISTINGS ────────────────────────
@app.route('/api/listings', methods=['GET'])
def get_listings():
    gender = request.args.get('gender', '')
    area = request.args.get('area', '')
    min_rent = request.args.get('min_rent', 0)
    max_rent = request.args.get('max_rent', 99999)
    apt_type = request.args.get('type', '')
    sort = request.args.get('sort', '')

    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM listings WHERE status = 'approved'"
    params = []

    if gender:
        query += " AND gender_preference = ?"
        params.append(gender)

    if area:
        query += " AND area = ?"
        params.append(area)

    if apt_type:
        query += " AND apartment_type = ?"
        params.append(apt_type)

    query += " AND rent >= ? AND rent <= ?"
    params.extend([int(min_rent), int(max_rent)])

    if sort == 'price_asc':
        query += " ORDER BY rent ASC"
    elif sort == 'price_desc':
        query += " ORDER BY rent DESC"
    else:
        query += " ORDER BY created_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    listings = []
    for row in rows:
        listing = dict(row)
        cursor.execute(
            'SELECT tag FROM listing_tags WHERE listing_id = ?', (listing['id'],))
        listing['tags'] = [t['tag'] for t in cursor.fetchall()]
        listings.append(listing)

    conn.close()
    return jsonify(listings)


# ─── GET SINGLE LISTING ───────────────────────────────
@app.route('/api/listings/<int:listing_id>', methods=['GET'])
def get_listing(listing_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM listings WHERE id = ?", (listing_id,))
    row = cursor.fetchone()

    if row is None:
        return jsonify({'error': 'Listing not found'}), 404

    listing = dict(row)
    cursor.execute(
        'SELECT tag FROM listing_tags WHERE listing_id = ?', (listing_id,))
    listing['tags'] = [t['tag'] for t in cursor.fetchall()]

    cursor.execute('SELECT name, phone FROM users WHERE id = ?',
                   (listing['user_id'],))
    owner = cursor.fetchone()
    listing['owner_name'] = owner['name']
    listing['owner_phone'] = owner['phone']

    conn.close()
    return jsonify(listing)


# ─── ADMIN — APPROVE LISTING ──────────────────────────
@app.route('/api/admin/listings/<int:listing_id>/approve', methods=['POST'])
def approve_listing(listing_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE listings SET status = 'approved' WHERE id = ?", (listing_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Listing approved'})


# ─── ADMIN — GET PENDING LISTINGS ─────────────────────
@app.route('/api/admin/listings/pending', methods=['GET'])
def get_pending_listings():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM listings WHERE status = 'pending'")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
