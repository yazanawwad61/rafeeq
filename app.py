import os
import secrets
import bleach
from flask import Flask, request, jsonify, session, render_template, redirect
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message as MailMessage
from PIL import Image
from werkzeug.utils import secure_filename
import sqlite3

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

# ── DATABASE ───────────────────────────────────────────────────────


def get_db():
    conn = sqlite3.connect('roommate.db')
    conn.row_factory = sqlite3.Row
    return conn


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def sanitize(text):
    return bleach.clean(str(text).strip(), tags=[], strip=True)


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            gender TEXT NOT NULL,
            phone TEXT,
            profile_pic TEXT,
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
    cursor.execute('SELECT COUNT(*) AS count FROM admins')
    if cursor.fetchone()['count'] == 0:
        cursor.execute('INSERT INTO admins (email, password) VALUES (?, ?)',
                       ('yazanawwad61@gmail.com', generate_password_hash('Rafeeq@2026')))

    conn.commit()
    conn.close()


init_db()

# ══════════════════════════════════════════════════════════════════
# FRONTEND ROUTES
# ══════════════════════════════════════════════════════════════════


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/sw.js')
def sw():
    return app.send_static_file('sw.js')


@app.route('/listing/<int:listing_id>')
def listing_page(listing_id):
    return render_template('listing.html', listing_id=listing_id)


@app.route('/messages')
def messages_page():
    return render_template('messages.html')


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
        cursor.execute('''
            INSERT INTO users (name, email, password, gender, phone, is_verified, verify_token)
            VALUES (?, ?, ?, ?, ?, 0, ?)
        ''', (name, email, hashed_password, gender, phone, verify_token))
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

    except sqlite3.IntegrityError:
        return jsonify({'error': 'An account with this email already exists'}), 409
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({'error': 'Something went wrong. Please try again.'}), 500


@app.route('/api/verify-email/<token>', methods=['GET'])
def verify_email(token):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE verify_token = ?', (token,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return jsonify({'error': 'Invalid or expired verification link'}), 400

        cursor.execute(
            'UPDATE users SET is_verified = 1, verify_token = NULL WHERE id = ?', (user['id'],))
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
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        if not user or not check_password_hash(user['password'], password):
            return jsonify({'error': 'Incorrect email or password'}), 401
        if not user['is_verified']:
            return jsonify({'error': 'Please verify your email before logging in'}), 403

        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_gender'] = user['gender']

        return jsonify({
            'message': 'Logged in successfully',
            'user': {'id': user['id'], 'name': user['name'], 'gender': user['gender']}
        }), 200

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        session.clear()
        return jsonify({'message': 'Logged out successfully'}), 200
    except Exception as e:
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/me', methods=['GET'])
def me():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not logged in'}), 401
        return jsonify({
            'id':     session['user_id'],
            'name':   session['user_name'],
            'gender': session['user_gender']
        }), 200
    except Exception as e:
        return jsonify({'error': 'Something went wrong.'}), 500


# ══════════════════════════════════════════════════════════════════
# LISTING ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route('/api/listings', methods=['POST'])
def create_listing():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401

        data = request.get_json()
        title = sanitize(data.get('title', ''))
        description = sanitize(data.get('description', ''))
        apartment_type = data.get('apartment_type', '').strip().lower()
        gender_preference = data.get('gender_preference', '').strip().lower()
        rent = data.get('rent')
        area = sanitize(data.get('area', ''))
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        rooms = data.get('rooms')
        tags = data.get('tags', [])

        if not all([title, apartment_type, gender_preference, rent, area]):
            return jsonify({'error': 'Title, type, gender preference, rent, and area are required'}), 400
        if apartment_type not in ('shared', 'private'):
            return jsonify({'error': 'apartment_type must be shared or private'}), 400
        if gender_preference not in ('male', 'female', 'any'):
            return jsonify({'error': 'gender_preference must be male, female, or any'}), 400

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO listings
                (user_id, title, description, apartment_type, gender_preference,
                 rent, area, latitude, longitude, rooms, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (session['user_id'], title, description, apartment_type,
              gender_preference, rent, area, latitude, longitude, rooms))

        listing_id = cursor.lastrowid
        for tag in tags:
            cursor.execute('INSERT INTO listing_tags (listing_id, tag) VALUES (?, ?)',
                           (listing_id, sanitize(tag)))

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
            query += ' AND l.gender_preference = ?'
            params.append(gender)
        if apt_type:
            query += ' AND l.apartment_type = ?'
            params.append(apt_type)
        if max_rent:
            query += ' AND l.rent <= ?'
            params.append(float(max_rent))

        if sort == 'price_asc':
            query += ' ORDER BY l.rent ASC'
        elif sort == 'price_desc':
            query += ' ORDER BY l.rent DESC'
        else:
            query += ' ORDER BY l.created_at DESC'

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(query, params)
        listings = cursor.fetchall()

        result = []
        for listing in listings:
            d = dict(listing)
            cursor.execute(
                'SELECT tag FROM listing_tags WHERE listing_id = ?', (listing['id'],))
            d['tags'] = [r['tag'] for r in cursor.fetchall()]
            cursor.execute(
                'SELECT photo_path FROM listing_photos WHERE listing_id = ?', (listing['id'],))
            d['photos'] = [r['photo_path'] for r in cursor.fetchall()]
            result.append(d)

        conn.close()
        return jsonify(result), 200

    except Exception as e:
        print(f"Get listings error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/listings/<int:listing_id>', methods=['GET'])
def get_listing(listing_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT l.*, u.name AS owner_name, u.phone AS owner_phone,
                   u.gender AS owner_gender, u.id AS owner_id
            FROM listings l
            JOIN users u ON l.user_id = u.id
            WHERE l.id = ?
        ''', (listing_id,))
        listing = cursor.fetchone()

        if not listing:
            conn.close()
            return jsonify({'error': 'Listing not found'}), 404

        d = dict(listing)
        cursor.execute(
            'SELECT tag FROM listing_tags WHERE listing_id = ?', (listing_id,))
        d['tags'] = [r['tag'] for r in cursor.fetchall()]
        cursor.execute(
            'SELECT photo_path FROM listing_photos WHERE listing_id = ?', (listing_id,))
        d['photos'] = [r['photo_path'] for r in cursor.fetchall()]

        conn.close()
        return jsonify(d), 200

    except Exception as e:
        print(f"Get listing error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/listings/<int:listing_id>/photos', methods=['POST'])
def upload_photo(listing_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT user_id FROM listings WHERE id = ?', (listing_id,))
        listing = cursor.fetchone()

        if not listing:
            conn.close()
            return jsonify({'error': 'Listing not found'}), 404
        if listing['user_id'] != session['user_id']:
            conn.close()
            return jsonify({'error': 'Not authorized'}), 403

        if 'photo' not in request.files:
            conn.close()
            return jsonify({'error': 'No photo provided'}), 400

        file = request.files['photo']
        if not allowed_file(file.filename):
            conn.close()
            return jsonify({'error': 'Only JPG, PNG and WEBP allowed'}), 400

        img = Image.open(file)
        img.verify()
        file.seek(0)
        img = Image.open(file)

        if img.width > MAX_IMAGE_WIDTH:
            ratio = MAX_IMAGE_WIDTH / img.width
            new_height = int(img.height * ratio)
            img = img.resize((MAX_IMAGE_WIDTH, new_height), Image.LANCZOS)

        filename = secure_filename(
            f"listing_{listing_id}_{secrets.token_hex(8)}.jpg")
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        img.convert('RGB').save(save_path, 'JPEG', quality=85)

        cursor.execute('INSERT INTO listing_photos (listing_id, photo_path) VALUES (?, ?)',
                       (listing_id, save_path))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Photo uploaded', 'path': save_path}), 201

    except Exception as e:
        print(f"Photo upload error: {e}")
        return jsonify({'error': 'Invalid image file'}), 400


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
        cursor.execute('''
            INSERT INTO reports (reporter_id, listing_id, reason, description)
            VALUES (?, ?, ?, ?)
        ''', (session['user_id'], listing_id, reason, description))
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

        cursor.execute('''
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
            GROUP BY m.listing_id,
                CASE WHEN m.sender_id = ? THEN m.receiver_id ELSE m.sender_id END
            ORDER BY m.created_at DESC
        ''', (user_id, user_id, user_id, user_id, user_id, user_id))

        conversations = [dict(row) for row in cursor.fetchall()]
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

        cursor.execute('''
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
        ''', (listing_id, user_id, other_user_id, other_user_id, user_id))

        messages = [dict(row) for row in cursor.fetchall()]

        cursor.execute('''
            UPDATE messages SET is_read = 1
            WHERE listing_id = ? AND receiver_id = ? AND sender_id = ?
        ''', (listing_id, user_id, other_user_id))
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
        cursor.execute('''
            INSERT INTO messages (sender_id, receiver_id, listing_id, message)
            VALUES (?, ?, ?, ?)
        ''', (session['user_id'], receiver_id, listing_id, message))
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
        cursor.execute('''
            INSERT INTO messages (sender_id, receiver_id, listing_id, message)
            VALUES (?, ?, ?, ?)
        ''', (user_id, receiver_id, listing_id, message))
        message_id = cursor.lastrowid

        cursor.execute('SELECT name FROM users WHERE id = ?', (user_id,))
        sender = cursor.fetchone()
        conn.commit()
        conn.close()

        room = f"chat_{listing_id}_{min(user_id, receiver_id)}_{max(user_id, receiver_id)}"
        emit('new_message', {
            'id':          message_id,
            'sender_id':   user_id,
            'sender_name': sender['name'],
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
        listings = [dict(row) for row in cursor.fetchall()]
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
            "UPDATE listings SET status = 'approved' WHERE id = ?", (listing_id,))
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
            "UPDATE listings SET status = 'rejected' WHERE id = ?", (listing_id,))
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
        reports = [dict(row) for row in cursor.fetchall()]
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
        cursor.execute('SELECT * FROM admins WHERE email = ?', (email,))
        admin = cursor.fetchone()
        conn.close()

        if not admin or not check_password_hash(admin['password'], password):
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

        cursor.execute("SELECT COUNT(*) AS count FROM users")
        total_users = cursor.fetchone()['count']

        cursor.execute(
            "SELECT COUNT(*) AS count FROM listings WHERE status = 'approved'")
        approved_listings = cursor.fetchone()['count']

        cursor.execute(
            "SELECT COUNT(*) AS count FROM listings WHERE status = 'pending'")
        pending_listings = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) AS count FROM messages")
        total_messages = cursor.fetchone()['count']

        cursor.execute(
            "SELECT COUNT(*) AS count FROM reports WHERE status = 'pending'")
        pending_reports = cursor.fetchone()['count']

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
        users = [dict(row) for row in cursor.fetchall()]
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
        admins = [dict(row) for row in cursor.fetchall()]
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
        cursor.execute('INSERT INTO admins (email, password) VALUES (?, ?)',
                       (email, generate_password_hash(password)))
        conn.commit()
        conn.close()
        return jsonify({'message': f'Admin {email} created successfully'}), 201

    except sqlite3.IntegrityError:
        return jsonify({'error': 'An admin with this email already exists'}), 409
    except Exception as e:
        return jsonify({'error': 'Something went wrong.'}), 500


@app.route('/api/admin/reports/<int:report_id>/resolve', methods=['POST'])
def resolve_report(report_id):
    try:
        if 'admin_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE reports SET status = 'resolved' WHERE id = ?", (report_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Report resolved'}), 200

    except Exception as e:
        return jsonify({'error': 'Something went wrong.'}), 500


# ══════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
