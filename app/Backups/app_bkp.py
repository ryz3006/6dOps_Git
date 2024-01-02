from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_session import Session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from app.config_bkp import Config
from flask import flash
import secrets
import smtplib
from email.mime.text import MIMEText
from custom_logger import setup_logger

# Set up logger for your script
logger = setup_logger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
Session(app)

# Database connection configuration
db_config = {
    "host": Config.DB_HOST,
    "user": Config.DB_USER,
    "password": Config.DB_PASSWORD,
    "database": Config.DB_DATABASE
}
logger.info(f"Connecting to database with configuration: {db_config}")

db = mysql.connector.connect(**db_config)

logger.info("Database connection successful!")

@app.before_request
def before_request():
    # Set last activity time in the session
    session['last_activity_time'] = datetime.utcnow()

    # Check for session timeout
    if 'username' in session and 'last_activity_time' in session:
        last_activity_time = session['last_activity_time']
        if datetime.utcnow() > last_activity_time + app.permanent_session_lifetime:
            # If more than session timeout duration of inactivity, logout the user
            logger.info(f"Session time exceeded, logging out the user: {session}")
            session.pop('username', None)
            session.pop('last_activity_time', None)


# Define a list of URL patterns you want to redirect to 'sign-in.html'
url_patterns = ['/', '/login', '/login.html', '/index.html', '/signin.html', '/sign-in.html', '/signin', '/sign-in']

for pattern in url_patterns:
    endpoint = f'handle_{pattern.replace("/", "_").strip("_")}'
    
    @app.route(pattern, endpoint=endpoint)
    def handle_multiple_urls():
        if 'username' in session:
            session.permanent = True  # Reset the session timeout on each request
            return redirect(url_for('dashboard'))
        elif request.path not in url_patterns:
            error_message = "You don't have any active session, please login first"
            return render_template('sign-in.html', error=error_message)
        else:
            # Check for success parameter from the signup route
            if request.args.get('success'):
                #flash('Signup successful! You can now log in.', 'success')
                return render_template('sign-in.html')
            else:
                return render_template('sign-in.html')


@app.route('/')
def home():
    return render_template('sign-in.html')

@app.route('/assets/<path:filename>')
def serve_static(filename):
    return send_from_directory('C:\\Users\\Dell\\Documents\\6dOps_Git\\6dOps_Git\\app\\assets\\', filename)

@app.route('/static/media/<path:filename>')
def serve_media(filename):
    return send_from_directory('C:\\Users\\Dell\\Documents\\6dOps_Git\\6dOps_Git\\app\\media\\', filename)

@app.route('/index') 
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('sign-in.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()

    if user and check_password_hash(user['password'], password):
        session['username'] = user['username']

        # Flash the success message
        success_message = request.args.get('success_message')
        if success_message:
            flash(success_message, 'success')
            logger.info(f"Login success for : {username}")
            print(f"Flashed success message: {success_message}")

        return redirect(url_for('dashboard'))
    else:
        flash('Invalid login credentials', 'error')
        logger.info(f"Login failed for : {username}")
        #print("Flashed error message: Invalid login credentials")
        return render_template('sign-in.html', error='Invalid login credentials')



@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html')
    else:
        return redirect(url_for('index'))
    
@app.route('/billing')
def billing():
    if 'username' in session:
        return render_template('billing.html')
    else:
        return redirect(url_for('index'))
    
@app.route('/rtl')
def rtl():
    if 'username' in session:
        return render_template('rtl.html')
    else:
        return redirect(url_for('index'))
    
@app.route('/tables')
def tables():
    if 'username' in session:
        return render_template('tables.html')
    else:
        return redirect(url_for('index'))

@app.route('/virtualreality')
def virtualreality():
    if 'username' in session:
        return render_template('virtual-reality.html')
    else:
        return redirect(url_for('index'))


@app.route('/profile')
def profile():
    if 'username' in session:
        return render_template('profile.html')
    else:
        return redirect(url_for('index'))
    
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Handle form submission
        email = request.form['email']
        username = request.form['username']

        cursor = db.cursor(dictionary=True)

        # Check if the user already exists
        cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('User already exists. Please choose a different username or email.', 'error')
            logger.info(f"Signup failed due to user already exist : {username}")
            return redirect(url_for('signup', error=True))

        # Generate a random password
        random_password = secrets.token_urlsafe(10)  # Adjust the password length as needed

        # Insert the new user into the database with the hashed password
        hashed_password = generate_password_hash(random_password, method='pbkdf2:sha256')
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, hashed_password))
        db.commit()

        # Send an email with the random password
        logger.info(f"Signup success for : {username} with password : {random_password}")
        send_email(email, f"Your new password: {random_password}", "Welcome to 6D Team Ops Portal")

        # Flash a success message and redirect to the login page
        flash('Registration successful! Check your email for the new password and login with the same.', 'success')
        return redirect(url_for('login', success=True))

    # If it's a GET request or form submission failed, render the signup page
    return render_template('signup.html')

def send_email(to, message, subject):
    # Configure the SMTP server using values from Config
    smtp_server = Config.EMAIL_SERVER
    smtp_port = Config.EMAIL_PORT
    smtp_username = Config.EMAIL_USERNAME
    smtp_password = Config.EMAIL_PASSWORD

    # Create a connection to the SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)

    # Compose the email
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = Config.EMAIL_SENDER
    msg['To'] = to

    # Send the email
    server.sendmail(Config.EMAIL_SENDER, [to], msg.as_string())

    # Close the connection
    server.quit()
    logger.info(f"Email sent for email id : {to} - with message : {message}")

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)