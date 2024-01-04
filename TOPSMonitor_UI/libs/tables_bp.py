from flask import Blueprint, render_template, redirect, url_for, session

tables_bp = Blueprint('tables', __name__)

@tables_bp.route('/tables')
def tables():
    if 'username' in session:
        return render_template('tables.html')
    else:
        return redirect(url_for('login_bp.login'))