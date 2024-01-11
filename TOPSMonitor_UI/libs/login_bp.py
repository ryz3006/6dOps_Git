# login_bp.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from libs.config import read_config

config = read_config()


login_bp = Blueprint('login_bp', __name__)

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    from app import db, logger
    if request.method == 'POST':
        # Handle the login form submission
        username = request.form['username']
        password = request.form['password']

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            return redirect(url_for('dashboard_bp.dashboard'))
        else:
            flash('Invalid login credentials', 'error')
            logger.info(f"Login failed for : {username}")
            return render_template('sign-in.html', error='Invalid login credentials')
    # If it's a 'GET' request, render the login page
    return render_template('sign-in.html', error=None)