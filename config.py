import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-secret-key-in-production')
    WTF_CSRF_ENABLED = True

    # MySQL via PyMySQL
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = ''
    DB_NAME = 'securitysystem'

    # Gmail SMTP (smtplib) — use a Gmail App Password, NOT your account password
    # Generate one at: https://myaccount.google.com/apppasswords (requires 2FA enabled)
    GMAIL_USER = os.environ.get('GMAIL_USER', 'walkeneha310@gmail.com')
    GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', 'jibvaeafkstybbus')
    ADMIN_EMAIL = 'walkeneha310@gmail.com'

    OTP_EXPIRY_MINUTES = 5
    MAX_LOGIN_ATTEMPTS = 3
