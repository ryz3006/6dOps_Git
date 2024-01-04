from flask import Blueprint, redirect, url_for, session

logout_bp = Blueprint('logout', __name__)

@logout_bp.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login_bp.login'))