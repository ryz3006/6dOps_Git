from email.mime.text import MIMEText
import smtplib
from flask import Flask, redirect, send_from_directory, url_for
from flask_session import Session



import mysql.connector
from custom_logger import setup_logger
from libs.config import read_config
import os

config = read_config()

flask_host = config.get("flask_host", "127.0.0.1")
flask_port = int(config.get("flask_port", 5000))

db_config = {
    "host": config.get("db_host", "127.0.0.1"),
    "user": config.get("db_user", ""),
    "port": int(config.get("db_port", 3306)),
    "password": config.get("db_password", ""),
    "database": config.get("db_database", "OPS")
}

# Set up logger for your script
logger = setup_logger(__name__)

app = Flask(__name__, template_folder='pages')
app.config.from_object(config)
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = config.get("secret_key", "Session#998899")  # Correct key here
logger.info(f"Got Secret Key: {app.secret_key}")
Session(app)

print(f"App Secret Key: {app.secret_key}")

logger.info(f"Reading configurations: {config}")
logger.info(f"Connecting to database with configuration: {db_config}")

db = mysql.connector.connect(**db_config)


logger.info("Database connection successful!")

# Register Blueprints
from libs.home_bp import home_bp
from libs.login_bp import login_bp
from libs.dashboard_bp import dashboard_bp
from libs.billing_bp import billing_bp
from libs.rtl_bp import rtl_bp
from libs.tables_bp import tables_bp
from libs.virtualreality_bp import virtualreality_bp
from libs.profile_bp import profile_bp
from libs.signup_bp import signup_bp
from libs.logout_bp import logout_bp

app.register_blueprint(home_bp)
app.register_blueprint(login_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(billing_bp)
app.register_blueprint(rtl_bp)
app.register_blueprint(tables_bp)
app.register_blueprint(virtualreality_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(signup_bp)
app.register_blueprint(logout_bp)

@app.route('/vendors/<path:filename>')
def serve_vendors(filename):
    return send_from_directory('vendors', filename)

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)


# Add the catch-all route at the end
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    # Redirect any unmatched URLs to the login screen
    return redirect(url_for('login_bp.login'))


if __name__ == '__main__':
    app.run(debug=True, host=flask_host, port=flask_port)