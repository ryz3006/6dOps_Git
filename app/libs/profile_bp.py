from flask import Blueprint, render_template, redirect, url_for, session

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile')
def profile():
    if 'username' in session:
        return render_template('profile.html')
    else:
        return redirect(url_for('login_bp.login'))