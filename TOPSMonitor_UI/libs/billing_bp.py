from flask import Blueprint, render_template, redirect, url_for, session
from libs.config import read_config

config = read_config()

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/billing')
def billing():
    if 'username' in session:
        return render_template('billing.html')
    else:
        return redirect(url_for('sign-in.html'))