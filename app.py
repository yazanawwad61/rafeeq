import os
import json
import secrets
import bleach
import sqlite3
from flask import Flask, request, jsonify, session, render_template, redirect
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message as MailMessage
from PIL import Image
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'rafeeq-dev-secret-2026')

# ── SOCKETIO ───────────────────────────────────────────────────────
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins='*')

# ── RATE LIMITER ───────────────────────────────────────────────────
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# ── EMAIL CONFIG ───────────────────────────────────────────────────
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'yazanawwad61@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ.get(
    'MAIL_PASSWORD', 'bzox obis orfo ackh')
app.config['MAIL_DEFAULT_SENDER'] = 'yazanawwad61@gmail.com'

mail = Mail(app)

# ── UPLOAD CONFIG ──────────────────────────────────────────────────
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_IMAGE_WIDTH = 1200

# ══════════════════════════════════════════════════════════════════
# DATABASE — PostgreSQL on Railway, SQLite locally
# ══════════════════════════════════════════════════════════════════

DATABASE_URL = os.environ.get('DATABASE_URL')


def get_db():
    if DATABASE_URL:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        return conn
    else:
        conn = sqlite3.connect('roommate.db')
        conn.row_factory = sqlite3.Row
        return conn


def q(sql):
    """Convert SQLite ? placeholders to PostgreSQL %s"""
    if DATABASE_URL:
        return sql.replace('?', '%s')
    return sql


def rows_to_dicts(cursor, rows):
    """Convert rows to list of dicts for both SQLite and PostgreSQL"""
    if DATABASE_URL:
        cols = [desc[0] for desc in cursor.description]
        return [dict(zip(cols, row)) for row in rows]
    return [dict(row) for row in rows]


def row_to_dict(cursor, row):
    """Convert single row to dict for both SQLite and PostgreSQL"""
    if DATABASE_URL:
        cols = [desc[0] for desc in cursor.description]
        return dict(zip(cols, row))
    return dict(row)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def sanitize(text):
    return bleach.clean(str(text).strip(), tags=[], strip=True)


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    if DATABASE_URL:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                gender TEXT NOT NULL,
                phone TEXT,
                profile_picture TEXT,
                is_verified INTEGER DEFAULT 0,
                verify_token TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS listings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                apartment_type TEXT NOT NULL,
                gender_preference TEXT NOT NULL,
                rent REAL NOT NULL,
                area TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                rooms INTEGER,
                status TEXT DEFAULT 'pending',
                id_photo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS listing_tags (
                id SERIAL PRIMARY KEY,
                listing_id INTEGER NOT NULL,
                tag TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS listing_photos (
                id SERIAL PRIMARY KEY,
                listing_id INTEGER NOT NULL,
                photo_path TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                listing_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id SERIAL PRIMARY KEY,
                reporter_id INTEGER NOT NULL,
                listing_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ratings (
                id SERIAL PRIMARY KEY,
                rater_id INTEGER NOT NULL,
                rated_user_id INTEGER NOT NULL,
                listing_id INTEGER NOT NULL,
                accuracy INTEGER,
                communication INTEGER,
                reliability INTEGER,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                gender TEXT NOT NULL,
                phone TEXT,
                profile_picture TEXT,
                is_verified INTEGER DEFAULT 0,
                verify_token TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                apartment_type TEXT NOT NULL,
                gender_preference TEXT NOT NULL,
                rent REAL NOT NULL,
                area TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                rooms INTEGER,
                status TEXT DEFAULT 'pending',
                id_photo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS listing_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id INTEGER NOT NULL,
                tag TEXT NOT NULL,
                FOREIGN KEY (listing_id) REFERENCES listings(id)
            );
            CREATE TABLE IF NOT EXISTS listing_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id INTEGER NOT NULL,
                photo_path TEXT NOT NULL,
                FOREIGN KEY (listing_id) REFERENCES listings(id)
            );
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
            );
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER NOT NULL,
                listing_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reporter_id) REFERENCES users(id),
                FOREIGN KEY (listing_id) REFERENCES listings(id)
            );
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rater_id INTEGER NOT NULL,
                rated_user_id INTEGER NOT NULL,
                listing_id INTEGER NOT NULL,
                accuracy INTEGER,
                communication INTEGER,
                reliability INTEGER,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rater_id) REFERENCES users(id),
                FOREIGN KEY (rated_user_id) REFERENCES users(id),
                FOREIGN KEY (listing_id) REFERENCES listings(id)
            );
        ''')

    # Create default admin if none exists
    cursor.execute('SELECT COUNT(*) FROM admins')
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute(
            q('INSERT INTO admins (email, password) VALUES (?, ?)'),
            ('yazanawwad61@gmail.com', generate_password_hash('Rafeeq@2026'))
        )

    conn.commit()
    conn.close()


init_db()


# ══════════════════════════════════════════════════════════════════
# FRONTEND ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html', mapbox_token=os.environ.get('MAPBOX_TOKEN', ''))


@app.route('/map')
def map_page():
    return render_template('map.html', mapbox_token=os.environ.get('MAPBOX_TOKEN', ''))


@app.route('/sw.js')
def sw():
    return app.send_static_file('sw.js')


@app.route('/listing/<int:listing_id>')
def listing_page(listing_id):
    return render_template('listing.html', listing_id=listing_id)


@app.route('/messages')
def messages_page():
    return render_template('messages.html')


@app.route('/my-listings')
def my_listings_page():
    return render_template('my_listings.html')


# ══════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route('/api/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        name = sanitize(data.get('name', ''))
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        gender = data.get('gender', '').strip().lower()
        phone = sanitize(data.get('phone', ''))

        if not all([name, email, password, gender]):
            return jsonify({'error': 'Name, email, password, and gender are required'}), 400
        if gender not in ('male', 'female'):
            return jsonify({'error': 'Gender must be male or female'}), 400
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        hashed_password = generate_password_hash(password)
        verify_token = secrets.token_urlsafe(32)

        conn = get_db()
        cursor = conn.cursor()
        username = generate_username(name, cursor)
        cursor.execute(q('''
            INSERT INTO users (name, email, password, gender, phone, username, is_verified, verify_token)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        '''), (name, email, hashed_password, gender, phone, username, verify_token))
        conn.commit()
        conn.close()

        try:
            verify_url = f"https://rafeeq-production.up.railway.app/api/verify-email/{verify_token}"
            msg = MailMessage(
                subject="Verify your Rafeeq account",
                recipients=[email],
                html=f"""
                <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;">
                    <h2 style="color:#2d6a4f;">Welcome to Rafeeq!</h2>
                    <p>Please verify your email to activate your account.</p>
                    <a href="{verify_url}"
                       style="background:#2d6a4f;color:white;padding:12px 24px;
                              text-decoration:none;border-radius:8px;display:inline-block;">
                        Verify My Email
                    </a>
                </div>"""
            )
            mail.send(msg)
        except Exception as mail_error:
            print(f"Email send failed: {mail_error}")

        return jsonify({'message': 'Account created. Please check your email to verify.'}), 201

    except Exception as e:
        print(f"Signup error: {e}")
        if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
            return jsonify({'error': 'An account with this email already exists'}), 409
        return jsonify({'error': 'Something went wrong. Please try again.'}), 500


@app.route('/api/verify-email/<token>', methods=['GET'])
def verify_email(token):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            q('SELECT id FROM users WHERE verify_token = ?'), (token,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return jsonify({'error': 'Invalid or expired verification link'}), 400

        user_id = row[0] if DATABASE_URL else row['id']
        cursor.execute(
            q('UPDATE users SET is_verified = 1, verify_token = NULL WHERE id = ?'), (user_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Email verified. You can now log in.'}), 200

    except Exception as e:
        print(f"Verify email error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(q('SELECT * FROM users WHERE email = ?'), (email,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({'error': 'Incorrect email or password'}), 401

        user = row_to_dict(cursor, row)

        if not check_password_hash(user['password'], password):
            return jsonify({'error': 'Incorrect email or password'}), 401
        if not user['is_verified']:
            return jsonify({'error': 'Please verify your email before logging in'}), 403

        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_gender'] = user['gender']

        return jsonify({
            'message': 'Logged in successfully',
            'user': {
                'id':              user['id'],
                'name':            user['name'],
                'gender':          user['gender'],
                'username':        user.get('username') or user['name'].lower().replace(' ', '.'),
                'phone':           user.get('phone') or '',
                'profile_picture': user.get('profile_picture') or ''
            }
        }), 200

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200


@app.route('/api/me', methods=['GET'])
def me():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            q('SELECT id, name, gender, phone, username, profile_picture FROM users WHERE id = ?'), (session['user_id'],))
        row = cursor.fetchone()
        conn.close()
        if not row:
            session.clear()
            return jsonify({'error': 'Not logged in'}), 401
        user = row_to_dict(cursor, row)
        return jsonify({
            'id':              user['id'],
            'name':            user['name'],
            'gender':          user['gender'],
            'phone':           user.get('phone', '') or '',
            'username':        user.get('username') or user['name'].lower().replace(' ', '.'),
            'profile_picture': user.get('profile_picture', '') or ''
        }), 200
    except Exception as e:
        print(f"Me error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500


# ══════════════════════════════════════════════════════════════════
# LISTING ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route('/api/listings', methods=['POST'])
def create_listing():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401

        # Reads from FormData (multipart)
        title = sanitize(request.form.get('title', ''))
        description = sanitize(request.form.get('description', ''))
        apartment_type = request.form.get('apartment_type', '').strip().lower()
        gender_preference = request.form.get(
            'gender_preference', '').strip().lower()
        rent = request.form.get('rent')
        area = sanitize(request.form.get('area', ''))
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        rooms = request.form.get('rooms')
        tags = json.loads(request.form.get('tags', '[]'))
        id_photo_file = request.files.get('id_photo')

        if not all([title, apartment_type, gender_preference, rent, area]):
            return jsonify({'error': 'Title, type, gender preference, rent, and area are required'}), 400
        if apartment_type not in ('shared', 'private'):
            return jsonify({'error': 'apartment_type must be shared or private'}), 400
        if gender_preference not in ('male', 'female', 'any'):
            return jsonify({'error': 'gender_preference must be male, female, or any'}), 400
        if not id_photo_file or not id_photo_file.filename:
            return jsonify({'error': 'National ID photo is required'}), 400

        # Store ID photo as base64 (no filesystem dependency)
        import base64
        import io
        id_b64 = None
        try:
            from PIL import Image as PILImage
            img = PILImage.open(id_photo_file)
            img.thumbnail((800, 800), PILImage.LANCZOS)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=85)
            buf.seek(0)
            id_b64 = 'data:image/jpeg;base64,' + \
                base64.b64encode(buf.read()).decode('utf-8')
        except Exception as e:
            print(f"ID photo processing error: {e}")
            return jsonify({'error': 'Could not process ID photo. Please try a different image.'}), 400

        conn = get_db()
        cursor = conn.cursor()

        if DATABASE_URL:
            cursor.execute('''
                INSERT INTO listings
                    (user_id, title, description, apartment_type, gender_preference,
                     rent, area, latitude, longitude, rooms, status, id_photo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s)
                RETURNING id
            ''', (session['user_id'], title, description, apartment_type,
                  gender_preference, rent, area,
                  float(latitude) if latitude else None,
                  float(longitude) if longitude else None,
                  int(rooms) if rooms else None, id_b64))
            listing_id = cursor.fetchone()[0]
        else:
            cursor.execute('''
                INSERT INTO listings
                    (user_id, title, description, apartment_type, gender_preference,
                     rent, area, latitude, longitude, rooms, status, id_photo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            ''', (session['user_id'], title, description, apartment_type,
                  gender_preference, rent, area,
                  float(latitude) if latitude else None,
                  float(longitude) if longitude else None,
                  int(rooms) if rooms else None, id_b64))
            listing_id = cursor.lastrowid

        for tag in tags:
            cursor.execute(q('INSERT INTO listing_tags (listing_id, tag) VALUES (?, ?)'),
                           (listing_id, sanitize(tag)))

        # Store apartment photos as base64
        photo_files = request.files.getlist('photos')
        for photo_file in photo_files[:10]:
            if photo_file and photo_file.filename:
                try:
                    from PIL import Image as PILImage
                    img = PILImage.open(photo_file)
                    img.thumbnail((1200, 1200), PILImage.LANCZOS)
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    buf = io.BytesIO()
                    img.save(buf, format='JPEG', quality=85)
                    buf.seek(0)
                    photo_b64 = 'data:image/jpeg;base64,' + \
                        base64.b64encode(buf.read()).decode('utf-8')
                    cursor.execute(q('INSERT INTO listing_photos (listing_id, photo_path) VALUES (?, ?)'),
                                   (listing_id, photo_b64))
                except Exception as pe:
                    print(f"Photo processing error: {pe}")

        conn.commit()
        conn.close()
        return jsonify({'message': 'Listing submitted for review', 'listing_id': listing_id}), 201

    except Exception as e:
        print(f"Create listing error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/listings', methods=['GET'])
def get_listings():
    try:
        gender = request.args.get('gender')
        apt_type = request.args.get('type')
        max_rent = request.args.get('max_rent')
        sort = request.args.get('sort', 'latest')

        query = '''
            SELECT l.*, u.name AS owner_name
            FROM listings l
            JOIN users u ON l.user_id = u.id
            WHERE l.status = 'approved'
        '''
        params = []

        if gender:
            query += q(' AND l.gender_preference = ?')
            params.append(gender)
        if apt_type:
            query += q(' AND l.apartment_type = ?')
            params.append(apt_type)
        if max_rent:
            query += q(' AND l.rent <= ?')
            params.append(float(max_rent))

        area = request.args.get('area')
        if area:
            query += q(' AND l.area = ?')
            params.append(area)

        if sort == 'price_asc':
            query += ' ORDER BY l.rent ASC'
        elif sort == 'price_desc':
            query += ' ORDER BY l.rent DESC'
        else:
            query += ' ORDER BY l.created_at DESC'

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(query, params)
        listings = rows_to_dicts(cursor, cursor.fetchall())

        if listings:
            ids = [l['id'] for l in listings]
            ph = ','.join(['%s' if DATABASE_URL else '?'] * len(ids))
            # Bulk fetch tags (1 query)
            cursor.execute(
                f'SELECT listing_id, tag FROM listing_tags WHERE listing_id IN ({ph})', ids)
            tags_map = {}
            for r in cursor.fetchall():
                lid, tag = (r[0], r[1]) if DATABASE_URL else (
                    r['listing_id'], r['tag'])
                tags_map.setdefault(lid, []).append(tag)
            # Bulk fetch photos (1 query)
            cursor.execute(
                f'SELECT listing_id, photo_path FROM listing_photos WHERE listing_id IN ({ph})', ids)
            photos_map = {}
            for r in cursor.fetchall():
                lid, photo = (r[0], r[1]) if DATABASE_URL else (
                    r['listing_id'], r['photo_path'])
                photos_map.setdefault(lid, []).append(photo)
            for listing in listings:
                listing['tags'] = tags_map.get(listing['id'], [])
                listing['photos'] = photos_map.get(listing['id'], [])
        else:
            for listing in listings:
                listing['tags'] = []
                listing['photos'] = []

        conn.close()
        return jsonify(listings), 200

    except Exception as e:
        print(f"Get listings error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/listings/<int:listing_id>', methods=['GET'])
def get_listing(listing_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(q('''
            SELECT l.*, u.name AS owner_name, u.phone AS owner_phone,
                   u.gender AS owner_gender, u.id AS owner_id,
                   u.username AS owner_username
            FROM listings l
            JOIN users u ON l.user_id = u.id
            WHERE l.id = ?
        '''), (listing_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return jsonify({'error': 'Listing not found'}), 404

        # Increment view counter
        cursor.execute(
            q('UPDATE listings SET views = COALESCE(views, 0) + 1 WHERE id = ?'), (listing_id,))
        conn.commit()

        d = row_to_dict(cursor, row)
        cursor.execute(
            q('SELECT tag FROM listing_tags WHERE listing_id = ?'), (listing_id,))
        d['tags'] = [r[0] if DATABASE_URL else r['tag']
                     for r in cursor.fetchall()]
        cursor.execute(
            q('SELECT photo_path FROM listing_photos WHERE listing_id = ?'), (listing_id,))
        d['photos'] = [r[0] if DATABASE_URL else r['photo_path']
                       for r in cursor.fetchall()]

        conn.close()
        return jsonify(d), 200

    except Exception as e:
        print(f"Get listing error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/listings/<int:listing_id>/report', methods=['POST'])
def report_listing(listing_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401

        data = request.get_json()
        reason = data.get('reason', '').strip().lower()
        description = sanitize(data.get('description', ''))

        if reason not in ('fake', 'harassment', 'discrimination', 'other'):
            return jsonify({'error': 'Invalid reason'}), 400

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(q('''
            INSERT INTO reports (reporter_id, listing_id, reason, description)
            VALUES (?, ?, ?, ?)
        '''), (session['user_id'], listing_id, reason, description))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Report submitted.'}), 201

    except Exception as e:
        print(f"Report error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500


# ══════════════════════════════════════════════════════════════════
# MESSAGING ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401

        user_id = session['user_id']
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(q('''
            SELECT
                m.listing_id,
                l.title AS listing_title,
                CASE WHEN m.sender_id = ? THEN m.receiver_id ELSE m.sender_id END AS other_user_id,
                CASE WHEN m.sender_id = ? THEN ru.name ELSE su.name END AS other_user_name,
                m.message AS last_message,
                m.created_at AS last_message_time,
                SUM(CASE WHEN m.is_read = 0 AND m.receiver_id = ? THEN 1 ELSE 0 END) AS unread_count
            FROM messages m
            JOIN listings l ON m.listing_id = l.id
            JOIN users su ON m.sender_id = su.id
            JOIN users ru ON m.receiver_id = ru.id
            WHERE m.sender_id = ? OR m.receiver_id = ?
            GROUP BY m.listing_id, l.title,
                CASE WHEN m.sender_id = ? THEN m.receiver_id ELSE m.sender_id END,
                CASE WHEN m.sender_id = ? THEN ru.name ELSE su.name END,
                m.message, m.created_at
            ORDER BY m.created_at DESC
        '''), (user_id, user_id, user_id, user_id, user_id, user_id, user_id))

        conversations = rows_to_dicts(cursor, cursor.fetchall())
        conn.close()
        return jsonify(conversations), 200

    except Exception as e:
        print(f"Get conversations error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/messages/<int:listing_id>/<int:other_user_id>', methods=['GET'])
def get_messages(listing_id, other_user_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401

        user_id = session['user_id']
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(q('''
            SELECT m.*, u.name AS sender_name
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.listing_id = ?
            AND (
                (m.sender_id = ? AND m.receiver_id = ?)
                OR
                (m.sender_id = ? AND m.receiver_id = ?)
            )
            ORDER BY m.created_at ASC
        '''), (listing_id, user_id, other_user_id, other_user_id, user_id))

        messages = rows_to_dicts(cursor, cursor.fetchall())

        cursor.execute(q('''
            UPDATE messages SET is_read = 1
            WHERE listing_id = ? AND receiver_id = ? AND sender_id = ?
        '''), (listing_id, user_id, other_user_id))
        conn.commit()
        conn.close()

        return jsonify(messages), 200

    except Exception as e:
        print(f"Get messages error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/messages', methods=['POST'])
@limiter.limit("50 per day")
def send_message_http():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401

        data = request.get_json()
        receiver_id = data.get('receiver_id')
        listing_id = data.get('listing_id')
        message = sanitize(data.get('message', ''))

        if not all([receiver_id, listing_id, message]):
            return jsonify({'error': 'receiver_id, listing_id, and message are required'}), 400
        if len(message) > 1000:
            return jsonify({'error': 'Message cannot exceed 1000 characters'}), 400

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(q('''
            INSERT INTO messages (sender_id, receiver_id, listing_id, message)
            VALUES (?, ?, ?, ?)
        '''), (session['user_id'], receiver_id, listing_id, message))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Message sent'}), 201

    except Exception as e:
        print(f"Send message error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500


# ══════════════════════════════════════════════════════════════════
# SOCKETIO EVENTS
# ══════════════════════════════════════════════════════════════════

@socketio.on('join_chat')
def handle_join(data):
    listing_id = data.get('listing_id')
    other_user_id = data.get('other_user_id')
    user_id = session.get('user_id')
    if not user_id:
        return
    room = f"chat_{listing_id}_{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
    join_room(room)
    emit('joined', {'room': room})


@socketio.on('send_message')
def handle_message(data):
    user_id = session.get('user_id')
    if not user_id:
        return

    receiver_id = data.get('receiver_id')
    listing_id = data.get('listing_id')
    message = sanitize(data.get('message', ''))

    if not message or len(message) > 1000:
        return

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(q('''
            INSERT INTO messages (sender_id, receiver_id, listing_id, message)
            VALUES (?, ?, ?, ?)
        '''), (user_id, receiver_id, listing_id, message))

        cursor.execute(q('SELECT name FROM users WHERE id = ?'), (user_id,))
        row = cursor.fetchone()
        sender_name = row[0] if DATABASE_URL else row['name']
        conn.commit()
        conn.close()

        room = f"chat_{listing_id}_{min(user_id, receiver_id)}_{max(user_id, receiver_id)}"
        emit('new_message', {
            'sender_id':   user_id,
            'sender_name': sender_name,
            'receiver_id': receiver_id,
            'listing_id':  listing_id,
            'message':     message,
            'created_at':  'just now'
        }, room=room)

    except Exception as e:
        print(f"SocketIO message error: {e}")


@socketio.on('leave_chat')
def handle_leave(data):
    listing_id = data.get('listing_id')
    other_user_id = data.get('other_user_id')
    user_id = session.get('user_id')
    if not user_id:
        return
    room = f"chat_{listing_id}_{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
    leave_room(room)


@app.route('/api/listings/<int:listing_id>/photos', methods=['POST'])
def upload_listing_photos(listing_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            q('SELECT user_id FROM listings WHERE id = ?'), (listing_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({'error': 'Listing not found'}), 404
        if row[0] != session['user_id']:
            conn.close()
            return jsonify({'error': 'Unauthorized'}), 403

        # Check current count
        cursor.execute(
            q('SELECT COUNT(*) FROM listing_photos WHERE listing_id = ?'), (listing_id,))
        current_count = cursor.fetchone()[0]

        photo_files = request.files.getlist('photos')
        remaining = max(0, 10 - current_count)
        saved = 0

        for photo_file in photo_files[:remaining]:
            if photo_file and photo_file.filename:
                try:
                    import base64
                    import io
                    from PIL import Image as PILImage
                    img = PILImage.open(photo_file)
                    img.thumbnail((1200, 1200), PILImage.LANCZOS)
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    buf = io.BytesIO()
                    img.save(buf, format='JPEG', quality=85)
                    buf.seek(0)
                    photo_b64 = 'data:image/jpeg;base64,' + \
                        base64.b64encode(buf.read()).decode('utf-8')
                    cursor.execute(q('INSERT INTO listing_photos (listing_id, photo_path) VALUES (?, ?)'),
                                   (listing_id, photo_b64))
                    saved += 1
                except Exception as pe:
                    print(f"Photo upload error: {pe}")

        conn.commit()
        conn.close()
        return jsonify({'message': f'{saved} photo(s) uploaded'}), 201
    except Exception as e:
        print(f"Upload photos error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/listings/<int:listing_id>/photos/remove', methods=['POST'])
def remove_listing_photo(listing_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            q('SELECT user_id FROM listings WHERE id = ?'), (listing_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({'error': 'Listing not found'}), 404
        if row[0] != session['user_id']:
            conn.close()
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.get_json()
        photo_path = data.get('photo_path', '')

        cursor.execute(q('DELETE FROM listing_photos WHERE listing_id = ? AND photo_path = ?'),
                       (listing_id, photo_path))
        conn.commit()
        conn.close()

        # Try to delete file from disk (not critical if it fails)
        try:
            if photo_path and not photo_path.startswith('http') and os.path.exists(photo_path):
                os.remove(photo_path)
        except Exception:
            pass

        return jsonify({'message': 'Photo removed'}), 200
    except Exception as e:
        print(f"Remove photo error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500

# ══════════════════════════════════════════════════════════════════
# PROFILE ROUTES
# ══════════════════════════════════════════════════════════════════


@app.route('/profile/<username>')
def profile_page(username):
    return render_template('profile.html')


@app.route('/api/profile/<username>', methods=['GET'])
def get_profile(username):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            q('SELECT id, name, username, profile_picture, created_at FROM users WHERE username = ?'), (username,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        user = row_to_dict(cursor, row)
        is_owner = 'user_id' in session and session['user_id'] == user['id']

        # Get listings — owner sees all, visitors see approved only
        if is_owner:
            cursor.execute(q('''
                SELECT id, title, rent, area, apartment_type, gender_preference,
                       rooms, status, views, created_at
                FROM listings WHERE user_id = ? ORDER BY created_at DESC
            '''), (user['id'],))
        else:
            cursor.execute(q('''
                SELECT id, title, rent, area, apartment_type, gender_preference,
                       rooms, status, views, created_at
                FROM listings WHERE user_id = ? AND status = 'approved' ORDER BY created_at DESC
            '''), (user['id'],))

        listings = rows_to_dicts(cursor, cursor.fetchall())

        if listings:
            ids = [l['id'] for l in listings]
            ph = ','.join(['%s' if DATABASE_URL else '?'] * len(ids))
            cursor.execute(
                f'SELECT listing_id, photo_path FROM listing_photos WHERE listing_id IN ({ph}) ORDER BY id', ids)
            photos = {}
            for r in cursor.fetchall():
                lid, path = (r[0], r[1]) if DATABASE_URL else (
                    r['listing_id'], r['photo_path'])
                photos.setdefault(lid, []).append(path)
            for l in listings:
                l['photos'] = photos.get(l['id'], [])

        insights = None
        if is_owner and listings:
            ids = [l['id'] for l in listings]
            ph = ','.join(['%s' if DATABASE_URL else '?'] * len(ids))
            cursor.execute(
                f'SELECT listing_id, COUNT(DISTINCT sender_id) as cnt FROM messages WHERE listing_id IN ({ph}) AND sender_id != {"%s" if DATABASE_URL else "?"} GROUP BY listing_id',
                ids + [user['id']]
            )
            msg_counts = {r[0]: r[1] for r in cursor.fetchall()}
            for l in listings:
                l['msg_count'] = msg_counts.get(l['id'], 0)
            insights = {
                'total_listings': len(listings),
                'total_views':    sum(l.get('views') or 0 for l in listings),
                'total_messages': sum(msg_counts.values()),
            }

        conn.close()
        return jsonify({'user': user, 'listings': listings, 'is_owner': is_owner, 'insights': insights}), 200
    except Exception as e:
        print(f"Profile error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/users/me', methods=['PUT'])
def update_user_profile():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        name = sanitize(request.form.get('name', '').strip())
        phone = sanitize(request.form.get('phone', '').strip())
        pic = request.files.get('profile_picture')
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        pic_b64 = None
        if pic and pic.filename:
            try:
                import base64
                from PIL import Image as PILImage
                import io
                img = PILImage.open(pic)
                img.thumbnail((400, 400), PILImage.LANCZOS)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=85)
                buf.seek(0)
                pic_b64 = 'data:image/jpeg;base64,' + \
                    base64.b64encode(buf.read()).decode('utf-8')
                print(f"Profile picture encoded, length: {len(pic_b64)}")
            except Exception as img_err:
                print(f"Profile picture processing error: {img_err}")
        conn = get_db()
        cursor = conn.cursor()
        if pic_b64:
            cursor.execute(q('UPDATE users SET name=?, phone=?, profile_picture=? WHERE id=?'),
                           (name, phone, pic_b64, session['user_id']))
        else:
            cursor.execute(q('UPDATE users SET name=?, phone=? WHERE id=?'),
                           (name, phone, session['user_id']))
        session['user_name'] = name
        conn.commit()
        conn.close()
        return jsonify({'message': 'Updated'}), 200
    except Exception as e:
        print(f"Update profile error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500

# ══════════════════════════════════════════════════════════════════
# ADMIN ROUTES
# ══════════════════════════════════════════════════════════════════


@app.route('/api/admin/listings/pending', methods=['GET'])
def get_pending_listings():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT l.*, u.name AS owner_name, u.email AS owner_email
            FROM listings l
            JOIN users u ON l.user_id = u.id
            WHERE l.status = 'pending'
            ORDER BY l.created_at ASC
        ''')
        listings = rows_to_dicts(cursor, cursor.fetchall())
        conn.close()
        return jsonify(listings), 200
    except Exception as e:
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/admin/listings/<int:listing_id>/approve', methods=['POST'])
def approve_listing(listing_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            q("UPDATE listings SET status = 'approved' WHERE id = ?"), (listing_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': f'Listing {listing_id} approved'}), 200
    except Exception as e:
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/admin/listings/<int:listing_id>/reject', methods=['POST'])
def reject_listing(listing_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            q("UPDATE listings SET status = 'rejected' WHERE id = ?"), (listing_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': f'Listing {listing_id} rejected'}), 200
    except Exception as e:
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/admin/reports', methods=['GET'])
def get_reports():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, u.name AS reporter_name, l.title AS listing_title
            FROM reports r
            JOIN users u ON r.reporter_id = u.id
            JOIN listings l ON r.listing_id = l.id
            WHERE r.status = 'pending'
            ORDER BY r.created_at ASC
        ''')
        reports = rows_to_dicts(cursor, cursor.fetchall())
        conn.close()
        return jsonify(reports), 200
    except Exception as e:
        return jsonify({'error': 'Something went wrong.'}), 500


# ══════════════════════════════════════════════════════════════════
# ADMIN AUTH ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route('/admin')
@app.route('/admin/login')
def admin_login_page():
    if 'admin_id' in session:
        return redirect('/admin/dashboard')
    return render_template('admin_login.html')


@app.route('/admin/dashboard')
def admin_dashboard_page():
    if 'admin_id' not in session:
        return redirect('/admin/login')
    return render_template('admin_dashboard.html')


@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(q('SELECT * FROM admins WHERE email = ?'), (email,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({'error': 'Incorrect email or password'}), 401

        admin = row_to_dict(cursor, row)

        if not check_password_hash(admin['password'], password):
            return jsonify({'error': 'Incorrect email or password'}), 401

        session['admin_id'] = admin['id']
        session['admin_email'] = admin['email']

        return jsonify({'message': 'Logged in successfully'}), 200

    except Exception as e:
        print(f"Admin login error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_email', None)
    return jsonify({'message': 'Logged out'}), 200


@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    try:
        if 'admin_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM listings WHERE status = 'approved'")
        approved_listings = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM listings WHERE status = 'pending'")
        pending_listings = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM reports WHERE status = 'pending'")
        pending_reports = cursor.fetchone()[0]

        conn.close()
        return jsonify({
            'total_users':       total_users,
            'approved_listings': approved_listings,
            'pending_listings':  pending_listings,
            'total_messages':    total_messages,
            'pending_reports':   pending_reports
        }), 200

    except Exception as e:
        print(f"Admin stats error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/admin/users', methods=['GET'])
def admin_get_users():
    try:
        if 'admin_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, email, gender, phone, is_verified, created_at
            FROM users ORDER BY created_at DESC
        ''')
        users = rows_to_dicts(cursor, cursor.fetchall())
        conn.close()
        return jsonify(users), 200

    except Exception as e:
        print(f"Admin get users error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/admin/admins', methods=['GET'])
def admin_get_admins():
    try:
        if 'admin_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, email FROM admins ORDER BY id ASC')
        admins = rows_to_dicts(cursor, cursor.fetchall())
        conn.close()
        return jsonify(admins), 200

    except Exception as e:
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/admin/admins', methods=['POST'])
def admin_create_admin():
    try:
        if 'admin_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(q('INSERT INTO admins (email, password) VALUES (?, ?)'),
                       (email, generate_password_hash(password)))
        conn.commit()
        conn.close()
        return jsonify({'message': f'Admin {email} created successfully'}), 201

    except Exception as e:
        if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
            return jsonify({'error': 'An admin with this email already exists'}), 409
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/admin/reports/<int:report_id>/resolve', methods=['POST'])
def resolve_report(report_id):
    try:
        if 'admin_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            q("UPDATE reports SET status = 'resolved' WHERE id = ?"), (report_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Report resolved'}), 200

    except Exception as e:
        return jsonify({'error': 'Something went wrong.'}), 500


# ══════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
