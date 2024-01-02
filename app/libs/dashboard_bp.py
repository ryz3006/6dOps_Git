from flask import Blueprint, render_template, redirect, url_for, session

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login_bp.login'))