from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
import secrets
from libs.email_utils import send_email

signup_bp = Blueprint('signup', __name__)

@signup_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    from app import db, logger
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
            return redirect(url_for('signup.signup', error=True))

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
        return redirect(url_for('login_bp.login', success=True))

    # If it's a GET request or form submission failed, render the signup page
    return render_template('signup.html')