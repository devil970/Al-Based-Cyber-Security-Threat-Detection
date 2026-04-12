# 🛡️ AI-Based Cyber Security Threat Detection System

A full-stack web application built with **Flask** and **MySQL** that provides intelligent user authentication, real-time threat detection, and a comprehensive admin control panel. The system monitors login behavior, detects suspicious activity, and automatically alerts administrators — simulating an AI-assisted cyber security layer.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Security Features](#security-features)
- [Admin Panel](#admin-panel)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This system is designed to detect and respond to cyber security threats in real time by monitoring user authentication patterns. It combines secure login mechanisms with automated threat response — including account locking, admin notifications, and support ticket management — to protect against brute-force attacks and unauthorized access.

---

## ✨ Features

### 👤 User Side
- Secure **registration** with email OTP verification
- **Login** with email or mobile number
- **Brute-force protection** — account locked after 3 failed attempts
- **Session tracking** — login time, logout time, session duration recorded
- **User dashboard** — view login history, session stats, and submit change requests
- **Support ticket system** — locked users can contact admin for account recovery
- **Change requests** — users can request password or email changes via admin

### 🔐 Admin Side
- Secure admin login with **OTP-based 2FA**
- **Admin dashboard** — view all registered users, login counts, last login
- **User detail view** — full login logs, session history, pending requests
- **Account management** — unlock, restrict, or delete user accounts
- **Action user requests** — approve password/email changes with automated user notification
- **Real-time email alerts** for:
  - New user registrations
  - User logins
  - Account lockouts
  - Support ticket submissions
  - Change request completions

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask 3.0 |
| Database | MySQL (via PyMySQL) |
| Frontend | HTML5, CSS3, JavaScript |
| Authentication | bcrypt password hashing |
| OTP / Email | Gmail SMTP (smtplib) |
| CSRF Protection | Flask-WTF |
| Session Management | Flask Sessions |

---

## 📁 Project Structure

```
securitysystem/
│
├── app.py                  # Main Flask application & all routes
├── config.py               # App configuration (DB, SMTP, secrets)
├── db.py                   # MySQL database connection helper
├── schema.sql              # Full database schema with table definitions
├── requirements.txt        # Python dependencies
│
├── static/
│   ├── style.css           # Global stylesheet
│   ├── script.js           # Frontend JavaScript
│   └── avatar.png          # Default user avatar
│
└── templates/
    ├── base.html           # Base layout template
    ├── register.html       # User registration page
    ├── login.html          # User login page
    ├── verify_otp.html     # OTP verification page
    ├── dashboard.html      # User dashboard
    ├── contact_admin.html  # Support ticket form
    └── admin/
        ├── login.html      # Admin login page
        ├── verify_otp.html # Admin OTP verification
        ├── dashboard.html  # Admin dashboard
        ├── user_detail.html# User detail & logs view
        └── setup.html      # One-time admin setup page
```

---

## 🗄️ Database Schema

The system uses **5 tables**:

| Table | Purpose |
|---|---|
| `users` | Stores registered user accounts and status |
| `otp_store` | Manages OTP codes with expiry and usage tracking |
| `login_logs` | Records every login attempt with IP, status, and session duration |
| `admin` | Admin account credentials |
| `support_tickets` | Stores user-submitted support/unlock requests |

---

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.8+
- XAMPP (MySQL + Apache) or any MySQL server
- Gmail account with [App Password](https://myaccount.google.com/apppasswords) enabled (requires 2FA)

### Step 1 — Clone the Repository

```bash
git clone https://github.com/devil970/Al-Based-Cyber-Security-Threat-Detection.git
cd Al-Based-Cyber-Security-Threat-Detection
```

### Step 2 — Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Set Up the Database

1. Start your MySQL server (via XAMPP or standalone)
2. Open **phpMyAdmin** or any MySQL client
3. Import the schema:

```bash
mysql -u root -p < schema.sql
```

Or paste the contents of `schema.sql` directly into phpMyAdmin's SQL tab.

### Step 5 — Configure the Application

Open `config.py` and update the following values:

```python
SECRET_KEY = 'your-strong-secret-key'

DB_HOST     = 'localhost'
DB_USER     = 'root'
DB_PASSWORD = ''           # Your MySQL password
DB_NAME     = 'securitysystem'

GMAIL_USER         = 'your-email@gmail.com'
GMAIL_APP_PASSWORD = 'your-gmail-app-password'
ADMIN_EMAIL        = 'admin-notification-email@gmail.com'
```

> ⚠️ **Never commit real credentials to GitHub.** Use environment variables in production (see [Configuration](#configuration)).

### Step 6 — Run the Application

```bash
python app.py
```

Visit: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🔧 Configuration

All settings are managed in `config.py`. For production, set these as **environment variables**:

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Flask session secret key | `change-this-secret-key-in-production` |
| `GMAIL_USER` | Gmail address for sending OTPs | — |
| `GMAIL_APP_PASSWORD` | Gmail App Password (not account password) | — |
| `OTP_EXPIRY_MINUTES` | OTP validity window | `5` |
| `MAX_LOGIN_ATTEMPTS` | Failed attempts before account lock | `3` |

**Setting environment variables (Windows):**
```cmd
set SECRET_KEY=your-secret-key
set GMAIL_USER=your-email@gmail.com
set GMAIL_APP_PASSWORD=your-app-password
```

**Setting environment variables (Linux/macOS):**
```bash
export SECRET_KEY=your-secret-key
export GMAIL_USER=your-email@gmail.com
export GMAIL_APP_PASSWORD=your-app-password
```

---

## 🚀 Usage

### User Flow

1. **Register** at `/register` — fill in name, email, mobile, and password
2. **Verify email** — enter the 6-digit OTP sent to your email
3. **Login** at `/login` — use email or mobile number + password
4. **Dashboard** — view your login history, session stats, and submit change requests
5. **Locked?** — visit `/contact-admin` to submit a support ticket

### Admin Flow

1. **Login** at `/admin/login` — enter admin credentials
2. **Verify OTP** — enter the OTP sent to the admin email
3. **Dashboard** — view all users, login activity, and pending requests
4. **Manage users** — unlock, restrict, delete accounts, or action change requests

### First-Time Admin Setup

If no admin exists, visit `/admin/setup` to create the initial admin account. This route is automatically blocked once an admin is created.

---

## 🔒 Security Features

| Feature | Implementation |
|---|---|
| Password Hashing | `bcrypt` with salt rounds |
| OTP Verification | 6-digit, 5-minute expiry, single-use |
| Brute-Force Protection | Account locked after 3 failed login attempts |
| Admin 2FA | OTP required on every admin login |
| CSRF Protection | Flask-WTF CSRF tokens on all forms |
| Session Management | Server-side Flask sessions |
| IP Logging | Every login attempt logs the client IP address |
| Admin Alerts | Real-time email notifications for all critical events |
| Account States | `active`, `locked`, `restricted` status management |

---

## 🖥️ Admin Panel

The admin panel provides full visibility and control:

- **User Overview** — total users, login counts, last login timestamps
- **Login Logs** — per-user login history with IP address, status, and session duration
- **Threat Detection** — identify users with repeated failed attempts or suspicious IPs
- **Account Actions** — unlock locked accounts, permanently restrict bad actors, delete users
- **Change Requests** — review and approve user-submitted password/email change requests
- **Support Tickets** — view and manage account recovery requests from locked users

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "Add: your feature description"`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a Pull Request

---

## 📄 License

This project is developed for academic and educational purposes.

---

## 👩‍💻 Author

Developed as part of an academic project on **AI-Based Cyber Security Threat Detection**.

---

> ⭐ If you found this project useful, please consider giving it a star on GitHub!
