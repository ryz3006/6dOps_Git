from flask import Blueprint, render_template, redirect, url_for, session

virtualreality_bp = Blueprint('virtualreality', __name__)

@virtualreality_bp.route('/virtualreality')
def virtualreality():
    if 'username' in session:
        return render_template('virtual-reality.html')
    else:
        return redirect(url_for('login_bp.login'))