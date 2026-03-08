import os
import secrets
from flask import Flask, request, jsonify, session, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from PIL import Image
from werkzeug.utils import secure_filename
import sqlite3

app = Flask(__name__)
app.secret_key = 'rafeeq-secret-key-2026'

# ── EMAIL CONFIG ───────────────────────────────────────────────────
# Replace these with your Gmail address and App Password
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'yazanawwad61@gmail.com'
app.config['MAIL_PASSWORD'] = 'bzox obis orfo ackh'
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

# ── FRONTEND ROUTES ────────────────────────────────────────────────


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/listing/<int:listing_id>')
def listing_page(listing_id):
    return render_template('listing.html', listing_id=listing_id)

# ══════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ══════════════════════════════════════════════════════════════════


@app.route('/api/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        gender = data.get('gender', '').strip().lower()
        phone = data.get('phone', '').strip()

        # Validation
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

        # Send verification email
        try:
            verify_url = f"http://127.0.0.1:5000/api/verify-email/{verify_token}"
            msg = Message(
                subject="Verify your Rafeeq account",
                recipients=[email],
                html=f"""
                <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
                    <h2 style="color: #2d6a4f;">Welcome to Rafeeq, {name}!</h2>
                    <p>Please verify your email address to activate your account.</p>
                    <a href="{verify_url}"
                       style="background:#2d6a4f; color:white; padding:12px 24px;
                              text-decoration:none; border-radius:8px; display:inline-block;">
                        Verify My Email
                    </a>
                    <p style="color:#888; margin-top:20px; font-size:13px;">
                        If you did not create a Rafeeq account, ignore this email.
                    </p>
                </div>
                """
            )
            mail.send(msg)
        except Exception as mail_error:
            print(f"Email send failed: {mail_error}")
            # Don't block signup if email fails — still create the account

        return jsonify({'message': 'Account created. Please check your email to verify your account.'}), 201

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

        return jsonify({'message': 'Email verified successfully. You can now log in.'}), 200

    except Exception as e:
        print(f"Verify email error: {e}")
        return jsonify({'error': 'Something went wrong. Please try again.'}), 500


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
            'user': {
                'id':     user['id'],
                'name':   user['name'],
                'gender': user['gender']
            }
        }), 200

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Something went wrong. Please try again.'}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        session.clear()
        return jsonify({'message': 'Logged out successfully'}), 200
    except Exception as e:
        print(f"Logout error: {e}")
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

        data = request.get_json()
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        apartment_type = data.get('apartment_type', '').strip().lower()
        gender_preference = data.get('gender_preference', '').strip().lower()
        rent = data.get('rent')
        area = data.get('area', '').strip()
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
                           (listing_id, tag.strip()))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Listing submitted for review', 'listing_id': listing_id}), 201

    except Exception as e:
        print(f"Create listing error: {e}")
        return jsonify({'error': 'Something went wrong. Please try again.'}), 500


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
            listing_dict = dict(listing)
            cursor.execute(
                'SELECT tag FROM listing_tags WHERE listing_id = ?', (listing['id'],))
            listing_dict['tags'] = [row['tag'] for row in cursor.fetchall()]
            cursor.execute(
                'SELECT photo_path FROM listing_photos WHERE listing_id = ?', (listing['id'],))
            listing_dict['photos'] = [row['photo_path']
                                      for row in cursor.fetchall()]
            result.append(listing_dict)

        conn.close()
        return jsonify(result), 200

    except Exception as e:
        print(f"Get listings error: {e}")
        return jsonify({'error': 'Something went wrong. Please try again.'}), 500


@app.route('/api/listings/<int:listing_id>', methods=['GET'])
def get_listing(listing_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT l.*, u.name AS owner_name, u.phone AS owner_phone, u.gender AS owner_gender
            FROM listings l
            JOIN users u ON l.user_id = u.id
            WHERE l.id = ?
        ''', (listing_id,))
        listing = cursor.fetchone()

        if not listing:
            conn.close()
            return jsonify({'error': 'Listing not found'}), 404

        listing_dict = dict(listing)

        cursor.execute(
            'SELECT tag FROM listing_tags WHERE listing_id = ?', (listing_id,))
        listing_dict['tags'] = [row['tag'] for row in cursor.fetchall()]

        cursor.execute(
            'SELECT photo_path FROM listing_photos WHERE listing_id = ?', (listing_id,))
        listing_dict['photos'] = [row['photo_path']
                                  for row in cursor.fetchall()]

        conn.close()
        return jsonify(listing_dict), 200

    except Exception as e:
        print(f"Get listing error: {e}")
        return jsonify({'error': 'Something went wrong. Please try again.'}), 500


# ── PHOTO UPLOAD ───────────────────────────────────────────────────
@app.route('/api/listings/<int:listing_id>/photos', methods=['POST'])
def upload_photo(listing_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401

        # Verify this listing belongs to the logged-in user
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

        if file.filename == '':
            conn.close()
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            conn.close()
            return jsonify({'error': 'Only JPG, PNG and WEBP files are allowed'}), 400

        # Open with Pillow — rejects non-image files automatically
        img = Image.open(file)
        img.verify()

        file.seek(0)
        img = Image.open(file)

        # Resize if too wide
        if img.width > MAX_IMAGE_WIDTH:
            ratio = MAX_IMAGE_WIDTH / img.width
            new_height = int(img.height * ratio)
            img = img.resize((MAX_IMAGE_WIDTH, new_height), Image.LANCZOS)

        # Save to uploads folder
        filename = secure_filename(
            f"listing_{listing_id}_{secrets.token_hex(8)}.jpg")
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        img.convert('RGB').save(save_path, 'JPEG', quality=85)

        # Save path to database
        cursor.execute('INSERT INTO listing_photos (listing_id, photo_path) VALUES (?, ?)',
                       (listing_id, save_path))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Photo uploaded successfully', 'path': save_path}), 201

    except Exception as e:
        print(f"Photo upload error: {e}")
        return jsonify({'error': 'Invalid image file or upload failed'}), 400


# ── REPORT A LISTING ───────────────────────────────────────────────
@app.route('/api/listings/<int:listing_id>/report', methods=['POST'])
def report_listing(listing_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401

        data = request.get_json()
        reason = data.get('reason', '').strip().lower()
        description = data.get('description', '').strip()

        if reason not in ('fake', 'harassment', 'discrimination', 'other'):
            return jsonify({'error': 'Reason must be: fake, harassment, discrimination, or other'}), 400

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reports (reporter_id, listing_id, reason, description)
            VALUES (?, ?, ?, ?)
        ''', (session['user_id'], listing_id, reason, description))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Report submitted. Our team will review it shortly.'}), 201

    except Exception as e:
        print(f"Report error: {e}")
        return jsonify({'error': 'Something went wrong. Please try again.'}), 500


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
        print(f"Pending listings error: {e}")
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
        print(f"Approve listing error: {e}")
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
        print(f"Reject listing error: {e}")
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
        print(f"Get reports error: {e}")
        return jsonify({'error': 'Something went wrong.'}), 500


# ══════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app.run(debug=True)
