# ⬡ NEURAL BREACH
### Academic Resource Network — Yugastr 2026 Hackathon

A full-stack academic resource sharing platform built with **Python Flask** + **HTML/CSS/JS**.

---

## 🚀 QUICK START

### 1. Install Dependencies
```bash
pip install flask werkzeug
```

### 2. Run the App
```bash
cd neural_breach
python app.py
```

### 3. Open Browser
```
http://localhost:5000
```

---

## ✅ MANDATORY FEATURES IMPLEMENTED

| Feature | Status |
|---|---|
| User Registration & Login | ✅ Email/password auth |
| User Profiles | ✅ Name, college, branch, semester, bio |
| Session Management | ✅ Flask sessions (persistent) |
| File Upload | ✅ PDF, DOCX, PPT, Images, ZIP |
| Resource Metadata | ✅ Title, subject, type, semester, year, tags |
| Edit/Delete Own Resources | ✅ Full CRUD |
| Access Control — Private | ✅ Same college only |
| Access Control — Public | ✅ Any user |
| Search by title/subject/tags | ✅ Full text search |
| Filter by subject/semester/type | ✅ Combined filters |
| Sort by latest/popular/rated | ✅ All 3 modes |
| Star Rating (1-5) | ✅ Interactive stars |
| Written Reviews | ✅ With edit support |
| One Review Per User | ✅ Enforced at DB level |
| Average Rating Display | ✅ On cards and detail page |

---

## 🏗️ PROJECT STRUCTURE

```
neural_breach/
├── app.py                  # Main Flask application
├── instance/
│   └── neural_breach.db    # SQLite database (auto-created)
├── static/
│   ├── css/main.css        # Cyberpunk UI styles
│   ├── js/main.js          # Frontend interactions
│   └── uploads/            # Uploaded files
└── templates/
    ├── base.html           # Base template with nav/footer
    ├── landing.html        # Landing page (unauthenticated)
    ├── login.html          # Login page
    ├── register.html       # Registration page
    ├── home.html           # Dashboard after login
    ├── upload.html         # Resource upload form
    ├── search.html         # Search & filter page
    ├── resource_detail.html # Resource detail + reviews
    ├── profile.html        # User profile dashboard
    ├── edit_profile.html   # Edit profile form
    └── edit_resource.html  # Edit resource form
```

---

## 🎨 TECH STACK

- **Backend**: Python Flask, SQLite (via sqlite3)
- **Frontend**: Vanilla HTML5, CSS3, JavaScript
- **Design**: Cyberpunk / Neural Network aesthetic
  - Fonts: Orbitron, Rajdhani, Share Tech Mono
  - Dark neon color scheme with scan-line effects
- **Auth**: Session-based with SHA-256 password hashing
- **Storage**: Local filesystem for uploaded files

---

## 👥 USER FLOWS

### Flow 1: Register & Upload
1. Visit `/` → Click "INITIALIZE ACCOUNT"
2. Fill: name, email, password, college, branch, semester
3. Go to Upload → Select file → Fill metadata → Choose privacy
4. Resource appears in dashboard and search

### Flow 2: Search & Download  
1. Login → Go to Search
2. Enter query + apply filters (subject, semester, type)
3. Click resource card → View details
4. Click "DOWNLOAD" → Leave a rating and review

### Flow 3: Access Control
- Private resources: Only accessible to same college users
- System checks college at profile vs resource upload
- Shows "This resource is private and only available to [College] students"

---

## 🔐 SECURITY FEATURES
- Password hashing (SHA-256)
- Secure filename handling (werkzeug)
- CSRF protection via form validation
- File type whitelist validation
- Ownership verification before edit/delete
- College-based access control enforcement

---

*Built for Yugastr 2026 Hackathon — Neural Breach Team*
