from datetime import timedelta

class Config:
    SECRET_KEY = 'SecretKey#8899'

    # Database configuration
    DB_HOST = "127.0.0.1"
    DB_USER = "opsuser"
    DB_PASSWORD = "opsuser@6Dtech"
    DB_DATABASE = "OPS"

    # Session configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)  # 5 minutes

    # Email configuration
    EMAIL_SERVER = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USERNAME = 'riyas.siddikk@6dtech.co.in'
    EMAIL_PASSWORD = 'qwertyryz'
    EMAIL_SENDER = 'riyas.siddikk@6dtech.co.in'
