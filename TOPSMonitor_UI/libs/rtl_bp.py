from flask import Blueprint, render_template, redirect, url_for, session

rtl_bp = Blueprint('rtl', __name__)

@rtl_bp.route('/rtl')
def rtl():
    if 'username' in session:
        return render_template('rtl.html')
    else:
        return redirect(url_for('login_bp.login'))