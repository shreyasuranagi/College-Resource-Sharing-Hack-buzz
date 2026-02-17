import os
import sqlite3
import hashlib
import secrets
import json
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename
from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify, send_from_directory, abort)

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'neural_breach.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'ppt', 'pptx', 'png', 'jpg', 'jpeg', 'txt', 'zip'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)


# ─── DATABASE ───────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            college TEXT NOT NULL,
            branch TEXT NOT NULL,
            semester TEXT NOT NULL,
            bio TEXT DEFAULT '',
            profile_pic TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            semester TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            year_batch TEXT NOT NULL,
            description TEXT DEFAULT '',
            tags TEXT DEFAULT '',
            privacy TEXT DEFAULT 'public',
            college TEXT NOT NULL,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            download_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            comment TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(resource_id, user_id),
            FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()


init_db()

# ─── MIGRATIONS (safe on existing DB) ───────────────────────────────────────
def run_migrations():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            resource_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, resource_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

run_migrations()


# ─── HELPERS ────────────────────────────────────────────────────────────────

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    if 'user_id' not in session:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    conn.close()
    return user


def get_resource_avg_rating(resource_id, conn):
    row = conn.execute(
        "SELECT AVG(rating) as avg, COUNT(*) as cnt FROM reviews WHERE resource_id = ?",
        (resource_id,)
    ).fetchone()
    return round(row['avg'] or 0, 1), row['cnt']


# ─── AUTH ROUTES ────────────────────────────────────────────────────────────

@app.route('/')
def index():
    user = get_current_user()
    if user:
        return redirect(url_for('home'))
    return render_template('landing.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        college = request.form.get('college', '').strip()
        branch = request.form.get('branch', '').strip()
        semester = request.form.get('semester', '').strip()
        bio = request.form.get('bio', '').strip()

        if not all([name, email, password, college, branch, semester]):
            flash('All required fields must be filled.', 'error')
            return render_template('register.html')

        conn = get_db()
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            flash('Email already registered. Please log in.', 'error')
            conn.close()
            return render_template('register.html')

        conn.execute(
            "INSERT INTO users (name, email, password_hash, college, branch, semester, bio) VALUES (?,?,?,?,?,?,?)",
            (name, email, hash_password(password), college, branch, semester, bio)
        )
        conn.commit()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_college'] = user['college']
        conn.close()
        flash(f'Welcome to Neural Breach, {name}!', 'success')
        return redirect(url_for('home'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND password_hash = ?",
            (email, hash_password(password))
        ).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_college'] = user['college']
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('home'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ─── MAIN APP ROUTES ────────────────────────────────────────────────────────

@app.route('/home')
@login_required
def home():
    user = get_current_user()
    conn = get_db()
    # Recent public resources + same college private
    resources = conn.execute("""
        SELECT r.*, u.name as uploader_name, u.college as uploader_college
        FROM resources r
        JOIN users u ON r.user_id = u.id
        WHERE r.privacy = 'public' OR r.college = ?
        ORDER BY r.created_at DESC LIMIT 12
    """, (user['college'],)).fetchall()

    result = []
    for res in resources:
        avg, cnt = get_resource_avg_rating(res['id'], conn)
        result.append(dict(res) | {'avg_rating': avg, 'review_count': cnt})

    stats = conn.execute("SELECT COUNT(*) as cnt FROM resources WHERE privacy='public'").fetchone()
    user_uploads = conn.execute("SELECT COUNT(*) as cnt FROM resources WHERE user_id=?", (user['id'],)).fetchone()
    conn.close()
    return render_template('home.html', user=user, resources=result,
                           public_count=stats['cnt'], user_uploads=user_uploads['cnt'])


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    user = get_current_user()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        subject = request.form.get('subject', '').strip()
        semester = request.form.get('semester', '').strip()
        resource_type = request.form.get('resource_type', '').strip()
        year_batch = request.form.get('year_batch', '').strip()
        description = request.form.get('description', '').strip()
        tags = request.form.get('tags', '').strip()
        privacy = request.form.get('privacy', 'public')

        if not all([title, subject, semester, resource_type, year_batch]):
            flash('Please fill all required fields.', 'error')
            return render_template('upload.html', user=user)

        if 'file' not in request.files or request.files['file'].filename == '':
            flash('Please select a file to upload.', 'error')
            return render_template('upload.html', user=user)

        file = request.files['file']
        if not allowed_file(file.filename):
            flash(f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}', 'error')
            return render_template('upload.html', user=user)

        original_filename = secure_filename(file.filename)
        unique_filename = f"{secrets.token_hex(8)}_{original_filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        file_size = os.path.getsize(filepath)

        conn = get_db()
        conn.execute("""
            INSERT INTO resources (user_id, title, subject, semester, resource_type,
            year_batch, description, tags, privacy, college, filename, original_filename, file_size)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (user['id'], title, subject, semester, resource_type, year_batch,
              description, tags, privacy, user['college'], unique_filename,
              original_filename, file_size))
        conn.commit()
        conn.close()
        flash('Resource uploaded successfully!', 'success')
        return redirect(url_for('home'))
    return render_template('upload.html', user=user)


@app.route('/search')
@login_required
def search():
    user = get_current_user()
    query = request.args.get('q', '').strip()
    subject = request.args.get('subject', '')
    semester = request.args.get('semester', '')
    resource_type = request.args.get('type', '')
    branch = request.args.get('branch', '')
    year_batch = request.args.get('year_batch', '')
    privacy = request.args.get('privacy', '')
    sort = request.args.get('sort', 'latest')

    conn = get_db()
    sql = """
        SELECT r.*, u.name as uploader_name, u.college as uploader_college, u.branch as uploader_branch
        FROM resources r
        JOIN users u ON r.user_id = u.id
        WHERE (r.privacy = 'public' OR r.college = ?)
    """
    params = [user['college']]

    if query:
        sql += " AND (r.title LIKE ? OR r.subject LIKE ? OR r.tags LIKE ? OR r.description LIKE ?)"
        q = f"%{query}%"
        params += [q, q, q, q]
    if subject:
        sql += " AND r.subject LIKE ?"
        params.append(f"%{subject}%")
    if semester:
        sql += " AND r.semester = ?"
        params.append(semester)
    if resource_type:
        sql += " AND r.resource_type = ?"
        params.append(resource_type)
    if branch:
        sql += " AND u.branch LIKE ?"
        params.append(f"%{branch}%")
    if year_batch:
        sql += " AND r.year_batch LIKE ?"
        params.append(f"%{year_batch}%")
    if privacy:
        sql += " AND r.privacy = ?"
        params.append(privacy)

    if sort == 'popular':
        sql += " ORDER BY r.download_count DESC"
    elif sort == 'rated':
        sql += " ORDER BY (SELECT AVG(rating) FROM reviews WHERE resource_id=r.id) DESC"
    else:
        sql += " ORDER BY r.created_at DESC"

    resources = conn.execute(sql, params).fetchall()
    result = []
    for res in resources:
        avg, cnt = get_resource_avg_rating(res['id'], conn)
        result.append(dict(res) | {'avg_rating': avg, 'review_count': cnt})
    conn.close()
    return render_template('search.html', user=user, resources=result,
                           query=query, subject=subject, semester=semester,
                           resource_type=resource_type, sort=sort)


@app.route('/resource/<int:resource_id>')
@login_required
def resource_detail(resource_id):
    user = get_current_user()
    conn = get_db()
    res = conn.execute("""
        SELECT r.*, u.name as uploader_name, u.college as uploader_college, u.branch as uploader_branch
        FROM resources r JOIN users u ON r.user_id = u.id
        WHERE r.id = ?
    """, (resource_id,)).fetchone()

    if not res:
        abort(404)

    # Access control
    if res['privacy'] == 'private' and res['college'] != user['college']:
        flash(f"This resource is private and only available to {res['college']} students.", 'error')
        return redirect(url_for('home'))

    reviews = conn.execute("""
        SELECT rv.*, u.name as reviewer_name
        FROM reviews rv JOIN users u ON rv.user_id = u.id
        WHERE rv.resource_id = ?
        ORDER BY rv.created_at DESC
    """, (resource_id,)).fetchall()

    avg, cnt = get_resource_avg_rating(resource_id, conn)
    user_review = conn.execute(
        "SELECT * FROM reviews WHERE resource_id=? AND user_id=?",
        (resource_id, user['id'])
    ).fetchone()
    is_bookmarked = conn.execute(
        "SELECT id FROM bookmarks WHERE user_id=? AND resource_id=?",
        (user['id'], resource_id)
    ).fetchone() is not None
    conn.close()
    return render_template('resource_detail.html', user=user, resource=dict(res),
                           reviews=reviews, avg_rating=avg, review_count=cnt,
                           user_review=user_review, is_bookmarked=is_bookmarked)


@app.route('/resource/<int:resource_id>/download')
@login_required
def download_resource(resource_id):
    user = get_current_user()
    conn = get_db()
    res = conn.execute("SELECT * FROM resources WHERE id = ?", (resource_id,)).fetchone()
    if not res:
        abort(404)
    if res['privacy'] == 'private' and res['college'] != user['college']:
        abort(403)
    conn.execute("UPDATE resources SET download_count = download_count + 1 WHERE id = ?", (resource_id,))
    conn.commit()
    conn.close()
    return send_from_directory(app.config['UPLOAD_FOLDER'], res['filename'],
                               as_attachment=True, download_name=res['original_filename'])


@app.route('/resource/<int:resource_id>/preview')
@login_required
def preview_resource(resource_id):
    user = get_current_user()
    conn = get_db()
    res = conn.execute("SELECT * FROM resources WHERE id = ?", (resource_id,)).fetchone()
    conn.close()
    if not res:
        abort(404)
    if res['privacy'] == 'private' and res['college'] != user['college']:
        abort(403)
    return send_from_directory(app.config['UPLOAD_FOLDER'], res['filename'])


@app.route('/resource/<int:resource_id>/bookmark', methods=['POST'])
@login_required
def toggle_bookmark(resource_id):
    user = get_current_user()
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM bookmarks WHERE user_id=? AND resource_id=?",
        (user['id'], resource_id)
    ).fetchone()
    if existing:
        conn.execute("DELETE FROM bookmarks WHERE user_id=? AND resource_id=?",
                     (user['id'], resource_id))
        flash('Bookmark removed.', 'info')
    else:
        conn.execute("INSERT INTO bookmarks (user_id, resource_id) VALUES (?,?)",
                     (user['id'], resource_id))
        flash('Resource bookmarked!', 'success')
    conn.commit()
    conn.close()
    return redirect(url_for('resource_detail', resource_id=resource_id))


@app.route('/resource/<int:resource_id>/review', methods=['POST'])
@login_required
def submit_review(resource_id):
    user = get_current_user()
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip()

    if not rating or rating < 1 or rating > 5:
        flash('Please provide a valid rating (1-5).', 'error')
        return redirect(url_for('resource_detail', resource_id=resource_id))

    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM reviews WHERE resource_id=? AND user_id=?",
        (resource_id, user['id'])
    ).fetchone()

    if existing:
        conn.execute(
            "UPDATE reviews SET rating=?, comment=? WHERE resource_id=? AND user_id=?",
            (rating, comment, resource_id, user['id'])
        )
        flash('Your review has been updated.', 'success')
    else:
        conn.execute(
            "INSERT INTO reviews (resource_id, user_id, rating, comment) VALUES (?,?,?,?)",
            (resource_id, user['id'], rating, comment)
        )
        flash('Review submitted successfully!', 'success')
    conn.commit()
    conn.close()
    return redirect(url_for('resource_detail', resource_id=resource_id))


@app.route('/resource/<int:resource_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_resource(resource_id):
    user = get_current_user()
    conn = get_db()
    res = conn.execute("SELECT * FROM resources WHERE id=? AND user_id=?",
                       (resource_id, user['id'])).fetchone()
    if not res:
        abort(403)
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        subject = request.form.get('subject', '').strip()
        semester = request.form.get('semester', '').strip()
        resource_type = request.form.get('resource_type', '').strip()
        year_batch = request.form.get('year_batch', '').strip()
        description = request.form.get('description', '').strip()
        tags = request.form.get('tags', '').strip()
        privacy = request.form.get('privacy', 'public')
        conn.execute("""
            UPDATE resources SET title=?, subject=?, semester=?, resource_type=?,
            year_batch=?, description=?, tags=?, privacy=? WHERE id=?
        """, (title, subject, semester, resource_type, year_batch, description, tags, privacy, resource_id))
        conn.commit()
        conn.close()
        flash('Resource updated successfully!', 'success')
        return redirect(url_for('resource_detail', resource_id=resource_id))
    conn.close()
    return render_template('edit_resource.html', user=user, resource=dict(res))


@app.route('/resource/<int:resource_id>/delete', methods=['POST'])
@login_required
def delete_resource(resource_id):
    user = get_current_user()
    conn = get_db()
    res = conn.execute("SELECT * FROM resources WHERE id=? AND user_id=?",
                       (resource_id, user['id'])).fetchone()
    if not res:
        abort(403)
    # Delete file from disk
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], res['filename'])
    if os.path.exists(filepath):
        os.remove(filepath)
    conn.execute("DELETE FROM resources WHERE id=?", (resource_id,))
    conn.commit()
    conn.close()
    flash('Resource deleted.', 'info')
    return redirect(url_for('profile'))


@app.route('/profile')
@login_required
def profile():
    user = get_current_user()
    conn = get_db()
    resources = conn.execute("""
        SELECT r.*, 
               (SELECT AVG(rating) FROM reviews WHERE resource_id=r.id) as avg_rating,
               (SELECT COUNT(*) FROM reviews WHERE resource_id=r.id) as review_count
        FROM resources r WHERE r.user_id=?
        ORDER BY r.created_at DESC
    """, (user['id'],)).fetchall()
    total_downloads = conn.execute(
        "SELECT SUM(download_count) as total FROM resources WHERE user_id=?", (user['id'],)
    ).fetchone()['total'] or 0
    conn.close()
    return render_template('profile.html', user=user, resources=resources,
                           total_downloads=total_downloads)


@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = get_current_user()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        college = request.form.get('college', '').strip()
        branch = request.form.get('branch', '').strip()
        semester = request.form.get('semester', '').strip()
        bio = request.form.get('bio', '').strip()
        conn = get_db()
        conn.execute("""
            UPDATE users SET name=?, college=?, branch=?, semester=?, bio=? WHERE id=?
        """, (name, college, branch, semester, bio, user['id']))
        conn.commit()
        conn.close()
        session['user_name'] = name
        session['user_college'] = college
        flash('Profile updated!', 'success')
        return redirect(url_for('profile'))
    return render_template('edit_profile.html', user=user)


# ─── API ENDPOINTS ──────────────────────────────────────────────────────────

@app.route('/api/resources')
@login_required
def api_resources():
    user = get_current_user()
    conn = get_db()
    resources = conn.execute("""
        SELECT r.id, r.title, r.subject, r.semester, r.resource_type, r.privacy,
               r.download_count, r.created_at, u.name as uploader, u.college
        FROM resources r JOIN users u ON r.user_id=u.id
        WHERE r.privacy='public' OR r.college=?
        ORDER BY r.created_at DESC LIMIT 20
    """, (user['college'],)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in resources])


@app.template_filter('timeago')
def timeago_filter(dt_str):
    if not dt_str:
        return ''
    try:
        dt = datetime.strptime(str(dt_str), '%Y-%m-%d %H:%M:%S')
        delta = datetime.now() - dt
        if delta.days > 365:
            return f"{delta.days // 365}y ago"
        elif delta.days > 30:
            return f"{delta.days // 30}mo ago"
        elif delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600}h ago"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60}m ago"
        return "just now"
    except:
        return str(dt_str)


@app.template_filter('file_icon')
def file_icon_filter(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    icons = {
        'pdf': '📄', 'docx': '📝', 'doc': '📝',
        'ppt': '📊', 'pptx': '📊', 'txt': '📃',
        'png': '🖼️', 'jpg': '🖼️', 'jpeg': '🖼️',
        'zip': '📦'
    }
    return icons.get(ext, '📁')


@app.template_filter('file_size_fmt')
def file_size_fmt(size):
    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size/1024:.1f}KB"
    return f"{size/(1024*1024):.1f}MB"


if __name__ == '__main__':
    app.run(debug=True, port=5000)
