from flask import Blueprint, render_template, redirect, url_for, session

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('sign-in.html')