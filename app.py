from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf.csrf import CSRFProtect
import bcrypt, random, string, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from functools import wraps
from db import get_db
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
csrf = CSRFProtect(app)

# ─── Helpers ────────────────────────────────────────────────────────────────

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def save_otp(identifier, otp, otp_type):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("UPDATE otp_store SET used=1 WHERE identifier=%s AND otp_type=%s AND used=0",
                        (identifier, otp_type))
            expires = datetime.now() + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)
            cur.execute("INSERT INTO otp_store (identifier, otp, otp_type, expires_at) VALUES (%s,%s,%s,%s)",
                        (identifier, otp, otp_type, expires))
        db.commit()
    finally:
        db.close()

def verify_otp(identifier, otp, otp_type):
    db = get_db()
    row = None
    try:
        with db.cursor() as cur:
            cur.execute("""SELECT id FROM otp_store
                           WHERE identifier=%s AND otp=%s AND otp_type=%s
                             AND used=0 AND expires_at > NOW()
                           ORDER BY id DESC LIMIT 1""",
                        (identifier, otp, otp_type))
            row = cur.fetchone()
            if row:
                cur.execute("UPDATE otp_store SET used=1 WHERE id=%s", (row['id'],))
        db.commit()
    finally:
        db.close()
    return bool(row)

def send_email_otp(email, otp):
    msg = MIMEMultipart()
    msg['From'] = Config.GMAIL_USER
    msg['To'] = email
    msg['Subject'] = 'Your OTP Code'
    msg.attach(MIMEText(
        f"Your OTP is: {otp}\nValid for {Config.OTP_EXPIRY_MINUTES} minutes.", 'plain'
    ))
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.ehlo()
        server.starttls()
        server.login(Config.GMAIL_USER, Config.GMAIL_APP_PASSWORD)
        server.sendmail(Config.GMAIL_USER, email, msg.as_string())

def send_admin_notification(subject, body):
    msg = MIMEMultipart()
    msg['From'] = Config.GMAIL_USER
    msg['To'] = Config.ADMIN_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.ehlo()
        server.starttls()
        server.login(Config.GMAIL_USER, Config.GMAIL_APP_PASSWORD)
        server.sendmail(Config.GMAIL_USER, Config.ADMIN_EMAIL, msg.as_string())

def send_admin_login_notification(user):
    login_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ip = request.remote_addr
    body = f"""A user has just logged in to the Security System.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  USER LOGIN NOTIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Name      : {user['name']}
  Email     : {user['email']}
  Mobile    : {user['mobile']}
  Status    : {user['status']}
  Login Time: {login_time}
  IP Address: {ip}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated notification.
"""
    send_admin_notification(f"[Login Alert] {user['name']} just logged in", body)

def send_admin_new_user_notification(user):
    registered_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    body = f"""A new user has registered on the Security System.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEW USER REGISTRATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Name        : {user['name']}
  Email       : {user['email']}
  Mobile      : {user['mobile']}
  Registered  : {registered_at}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated notification.
"""
    send_admin_notification(f"[New User] {user['name']} just registered", body)

def send_admin_locked_notification(user):
    locked_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ip = request.remote_addr
    body = f"""A user account has been locked due to too many failed login attempts.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ACCOUNT LOCKED ALERT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Name        : {user['name']}
  Email       : {user['email']}
  Mobile      : {user['mobile']}
  Locked At   : {locked_at}
  IP Address  : {ip}
  Failed Attempts: {user['failed_attempts'] + 1}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Please review this account in the admin dashboard.
This is an automated notification.
"""
    send_admin_notification(f"[Account Locked] {user['name']}'s account has been locked", body)


def log_login(user_id, status):
    ip = request.remote_addr
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("INSERT INTO login_logs (user_id, ip_address, status) VALUES (%s,%s,%s)",
                        (user_id, ip, status))
        db.commit()
    finally:
        db.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def get_user_by_identifier(identifier):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE email=%s OR mobile=%s", (identifier, identifier))
        user = cur.fetchone()
    db.close()
    return user

# ─── Auth Routes ────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        mobile = request.form['mobile'].strip()
        password = request.form['password']

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE email=%s OR mobile=%s", (email, mobile))
                if cur.fetchone():
                    flash('Email or mobile already registered.', 'danger')
                    return render_template('register.html')

                pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                cur.execute("""INSERT INTO users (name, email, mobile, password_hash)
                               VALUES (%s,%s,%s,%s)""", (name, email, mobile, pw_hash))
            db.commit()
        finally:
            db.close()

        otp = generate_otp()
        save_otp(email, otp, 'email')
        send_email_otp(email, otp)

        session['reg_email'] = email
        send_admin_new_user_notification({'name': name, 'email': email, 'mobile': mobile})
        return redirect(url_for('verify_email_otp'))

    return render_template('register.html')

@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email_otp():
    email = session.get('reg_email')
    if not email:
        return redirect(url_for('register'))

    if request.method == 'POST':
        otp = request.form['otp'].strip()
        if verify_otp(email, otp, 'email'):
            db = get_db()
            try:
                with db.cursor() as cur:
                    cur.execute("UPDATE users SET email_verified=1 WHERE email=%s", (email,))
                db.commit()
            finally:
                db.close()
            session.pop('reg_email', None)
            flash('Registration complete! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid or expired OTP.', 'danger')

    return render_template('verify_otp.html', target=email, otp_expiry=Config.OTP_EXPIRY_MINUTES)

@app.route('/resend-otp')
def resend_otp():
    email = session.get('reg_email')
    if email:
        otp = generate_otp()
        save_otp(email, otp, 'email')
        send_email_otp(email, otp)
        flash('OTP resent to email.', 'info')
    return redirect(url_for('verify_email_otp'))

@app.route('/contact-admin', methods=['GET', 'POST'])
def contact_admin():
    if request.method == 'POST':
        name    = request.form['name'].strip()
        email   = request.form['email'].strip().lower()
        problem = request.form['problem'].strip()

        ticket_number = ''.join(random.choices(string.digits, k=10))

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    "INSERT INTO support_tickets (ticket_number, name, email, problem) VALUES (%s,%s,%s,%s)",
                    (ticket_number, name, email, problem)
                )
            db.commit()
        finally:
            db.close()

        # Mail to user
        user_body = f"""Hello {name},

Your support request has been received.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  YOUR TICKET DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Ticket Number : {ticket_number}
  Name          : {name}
  Email         : {email}
  Problem       : {problem}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Please save your ticket number for future reference.
Our admin will review and unlock your account shortly.
"""
        msg_user = MIMEMultipart()
        msg_user['From']    = Config.GMAIL_USER
        msg_user['To']      = email
        msg_user['Subject'] = f"Support Ticket #{ticket_number} Received"
        msg_user.attach(MIMEText(user_body, 'plain'))

        # Mail to admin
        admin_body = f"""A locked user has submitted a support request.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEW SUPPORT TICKET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Ticket Number : {ticket_number}
  Name          : {name}
  Email         : {email}
  Problem       : {problem}
  Submitted At  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Please review and unlock the account from the admin dashboard.
"""
        msg_admin = MIMEMultipart()
        msg_admin['From']    = Config.GMAIL_USER
        msg_admin['To']      = Config.ADMIN_EMAIL
        msg_admin['Subject'] = f"[Support Ticket #{ticket_number}] {name} needs help"
        msg_admin.attach(MIMEText(admin_body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.ehlo()
            server.starttls()
            server.login(Config.GMAIL_USER, Config.GMAIL_APP_PASSWORD)
            server.sendmail(Config.GMAIL_USER, email, msg_user.as_string())
            server.sendmail(Config.GMAIL_USER, Config.ADMIN_EMAIL, msg_admin.as_string())

        return render_template('contact_admin.html', ticket_number=ticket_number, submitted=True)

    return render_template('contact_admin.html', submitted=False)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier'].strip()
        password = request.form['password']
        user = get_user_by_identifier(identifier)

        if not user:
            flash('Invalid credentials.', 'danger')
            return render_template('login.html')

        if user['status'] == 'restricted':
            flash('Your account has been permanently restricted.', 'danger')
            return render_template('login.html')

        if user['status'] == 'locked':
            log_login(user['id'], 'locked')
            flash('Account locked due to too many failed attempts. Contact admin.', 'warning')
            return render_template('login.html', locked=True)

        if not user['email_verified']:
            flash('Please complete OTP verification first.', 'warning')
            return render_template('login.html')

        if bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            db = get_db()
            try:
                with db.cursor() as cur:
                    cur.execute("UPDATE users SET failed_attempts=0 WHERE id=%s", (user['id'],))
                db.commit()
            finally:
                db.close()
            log_login(user['id'], 'success')
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['login_time'] = datetime.now().isoformat()
            send_admin_login_notification(user)
            return redirect(url_for('dashboard'))
        else:
            db = get_db()
            try:
                with db.cursor() as cur:
                    new_attempts = user['failed_attempts'] + 1
                    if new_attempts >= Config.MAX_LOGIN_ATTEMPTS:
                        cur.execute("UPDATE users SET failed_attempts=%s, status='locked' WHERE id=%s",
                                    (new_attempts, user['id']))
                        db.commit()
                        log_login(user['id'], 'locked')
                        send_admin_locked_notification(user)
                        flash('Too many failed attempts. Account locked.', 'danger')
                    else:
                        cur.execute("UPDATE users SET failed_attempts=%s WHERE id=%s",
                                    (new_attempts, user['id']))
                        db.commit()
                        log_login(user['id'], 'failed')
                        remaining = Config.MAX_LOGIN_ATTEMPTS - new_attempts
                        flash(f'Invalid password. {remaining} attempt(s) remaining.', 'danger')
            finally:
                db.close()

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
            user = cur.fetchone()
            cur.execute("SELECT * FROM user_requests WHERE user_id=%s ORDER BY created_at DESC", (user_id,))
            requests_list = cur.fetchall()
            cur.execute("""
                SELECT login_time, logout_time, ip_address, status, session_duration
                FROM login_logs WHERE user_id=%s ORDER BY login_time DESC LIMIT 5
            """, (user_id,))
            recent_logs = cur.fetchall()
            cur.execute("SELECT COUNT(*) as total FROM login_logs WHERE user_id=%s AND status='success'", (user_id,))
            total_logins = cur.fetchone()['total']
            cur.execute("SELECT COUNT(*) as total FROM login_logs WHERE user_id=%s AND status='failed'", (user_id,))
            failed_logins = cur.fetchone()['total']
            cur.execute("SELECT AVG(session_duration) as avg_dur FROM login_logs WHERE user_id=%s AND session_duration IS NOT NULL", (user_id,))
            avg_row = cur.fetchone()
            avg_session = int(avg_row['avg_dur']) if avg_row['avg_dur'] else 0
    finally:
        db.close()
    return render_template('dashboard.html',
        user=user,
        name=session['user_name'],
        requests=requests_list,
        recent_logs=recent_logs,
        total_logins=total_logins,
        failed_logins=failed_logins,
        avg_session=avg_session,
        login_time=session.get('login_time')
    )

@app.route('/user-request', methods=['POST'])
@login_required
def user_request():
    name         = request.form['name'].strip()
    email        = request.form['email'].strip().lower()
    request_type = request.form['request_type']
    new_value    = request.form['new_value'].strip()

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO user_requests (user_id, name, email, request_type, new_value) VALUES (%s,%s,%s,%s,%s)",
                (session['user_id'], name, email, request_type, new_value)
            )
        db.commit()
    finally:
        db.close()

    label = 'Change Password' if request_type == 'change_password' else 'Change Email'
    body = f"""A user has submitted a change request.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  USER CHANGE REQUEST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Name         : {name}
  Email        : {email}
  Request Type : {label}
  New Value    : {new_value}
  Submitted At : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Please review and action this from the admin dashboard.
"""
    send_admin_notification(f"[User Request] {name} requested {label}", body)
    flash('Your request has been submitted. Admin will action it shortly.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    user_id = session['user_id']
    login_time = session.get('login_time')
    if login_time:
        duration = int((datetime.now() - datetime.fromisoformat(login_time)).total_seconds())
        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute("""UPDATE login_logs SET logout_time=NOW(), session_duration=%s
                               WHERE user_id=%s AND logout_time IS NULL
                               ORDER BY id DESC LIMIT 1""", (duration, user_id))
            db.commit()
        finally:
            db.close()
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

# ─── Admin Routes ────────────────────────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute("SELECT * FROM admin WHERE username=%s", (username,))
                admin = cur.fetchone()
        finally:
            db.close()
        if admin and bcrypt.checkpw(password.encode(), admin['password_hash'].encode()):
            otp = generate_otp()
            save_otp(admin['email'], otp, 'email')
            send_email_otp(admin['email'], otp)
            session['admin_pending_id'] = admin['id']
            session['admin_pending_name'] = admin['username']
            session['admin_pending_email'] = admin['email']
            return redirect(url_for('admin_verify_otp'))
        flash('Invalid admin credentials.', 'danger')
    return render_template('admin/login.html')

@app.route('/admin/verify-otp', methods=['GET', 'POST'])
def admin_verify_otp():
    email = session.get('admin_pending_email')
    if not email:
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        otp = request.form['otp'].strip()
        if verify_otp(email, otp, 'email'):
            session['admin_id']   = session.pop('admin_pending_id')
            session['admin_name'] = session.pop('admin_pending_name')
            session.pop('admin_pending_email', None)
            return redirect(url_for('admin_dashboard'))
        flash('Invalid or expired OTP.', 'danger')
    return render_template('admin/verify_otp.html', email=email, otp_expiry=Config.OTP_EXPIRY_MINUTES)

@app.route('/admin/resend-otp')
def admin_resend_otp():
    email = session.get('admin_pending_email')
    if email:
        otp = generate_otp()
        save_otp(email, otp, 'email')
        send_email_otp(email, otp)
        flash('OTP resent to admin email.', 'info')
    return redirect(url_for('admin_verify_otp'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""SELECT u.id, u.name, u.email, u.mobile, u.status,
                                  u.failed_attempts, u.created_at,
                                  COUNT(l.id) as total_logins,
                                  MAX(l.login_time) as last_login
                           FROM users u
                           LEFT JOIN login_logs l ON l.user_id = u.id AND l.status='success'
                           GROUP BY u.id ORDER BY u.created_at DESC""")
            users = cur.fetchall()
    finally:
        db.close()
    return render_template('admin/dashboard.html', users=users)

@app.route('/admin/user/<int:user_id>')
@admin_required
def admin_user_detail(user_id):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
            user = cur.fetchone()
            cur.execute("""SELECT login_time, logout_time, ip_address, status, session_duration
                           FROM login_logs WHERE user_id=%s ORDER BY login_time DESC LIMIT 50""",
                        (user_id,))
            logs = cur.fetchall()
            cur.execute("SELECT * FROM user_requests WHERE user_id=%s ORDER BY created_at DESC", (user_id,))
            user_reqs = cur.fetchall()
    finally:
        db.close()
    return render_template('admin/user_detail.html', user=user, logs=logs, user_reqs=user_reqs)

@app.route('/admin/user/<int:user_id>/unlock', methods=['POST'])
@admin_required
def admin_unlock(user_id):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("UPDATE users SET status='active', failed_attempts=0 WHERE id=%s", (user_id,))
        db.commit()
    finally:
        db.close()
    flash('User account unlocked.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def admin_delete(user_id):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("DELETE FROM login_logs WHERE user_id=%s", (user_id,))
            cur.execute("DELETE FROM user_requests WHERE user_id=%s", (user_id,))
            cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
        db.commit()
    finally:
        db.close()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/request/<int:req_id>/action', methods=['POST'])
@admin_required
def admin_action_request(req_id):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM user_requests WHERE id=%s", (req_id,))
            req = cur.fetchone()
        if not req or req['status'] == 'done':
            flash('Request not found or already actioned.', 'warning')
            return redirect(url_for('admin_dashboard'))

        with db.cursor() as cur:
            if req['request_type'] == 'change_password':
                pw_hash = bcrypt.hashpw(req['new_value'].encode(), bcrypt.gensalt()).decode()
                cur.execute("UPDATE users SET password_hash=%s WHERE id=%s", (pw_hash, req['user_id']))
                label    = 'Password'
                notified = 'Your password has been updated by the admin.'
            else:
                cur.execute("UPDATE users SET email=%s WHERE id=%s", (req['new_value'], req['user_id']))
                label    = 'Email'
                notified = f'Your email has been updated to {req["new_value"]} by the admin.'

            cur.execute("UPDATE user_requests SET status='done' WHERE id=%s", (req_id,))
        db.commit()
    finally:
        db.close()

    body = f"""Hello {req['name']},

Your {label} change request has been completed by the admin.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  REQUEST COMPLETED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  {notified}
  Actioned At : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If you did not make this request, contact admin immediately.
"""
    msg = MIMEMultipart()
    msg['From']    = Config.GMAIL_USER
    msg['To']      = req['email']
    msg['Subject'] = f'Your {label} Change Request Has Been Completed'
    msg.attach(MIMEText(body, 'plain'))
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.ehlo()
        server.starttls()
        server.login(Config.GMAIL_USER, Config.GMAIL_APP_PASSWORD)
        server.sendmail(Config.GMAIL_USER, req['email'], msg.as_string())

    flash(f'{label} updated and user notified.', 'success')
    return redirect(url_for('admin_user_detail', user_id=req['user_id']))

@app.route('/admin/user/<int:user_id>/restrict', methods=['POST'])
@admin_required
def admin_restrict(user_id):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("UPDATE users SET status='restricted' WHERE id=%s", (user_id,))
        db.commit()
    finally:
        db.close()
    flash('User permanently restricted.', 'warning')
    return redirect(url_for('admin_dashboard'))

# ─── Admin Setup Helper ──────────────────────────────────────────────────────

@app.route('/admin/setup', methods=['GET', 'POST'])
def admin_setup():
    """One-time admin account creation. Remove this route after setup."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM admin")
            if cur.fetchone()['cnt'] > 0:
                return "Admin already exists.", 403
    finally:
        db.close()

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        email = request.form['email'].strip()
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute("INSERT INTO admin (username, password_hash, email) VALUES (%s,%s,%s)",
                            (username, pw_hash, email))
            db.commit()
        finally:
            db.close()
        flash('Admin created. Please login.', 'success')
        return redirect(url_for('admin_login'))

    return render_template('admin/setup.html')

if __name__ == '__main__':
    app.run(debug=True)
