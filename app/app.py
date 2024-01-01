from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'SecretKey#8899'

# Database connection configuration
db = mysql.connector.connect(
    host="127.0.0.1",
    user="opsuser",
    password="opsuser@6Dtech",
    database="OPS"
)

# Define a list of URL patterns you want to redirect to 'sign-in.html'
url_patterns = ['/', '/login', '/login.html', '/index.html', '/signin.html', '/sign-in.html', '/signin', '/sign-in']

for pattern in url_patterns:
    endpoint = f'handle_{pattern.replace("/", "_").strip("_")}'
    
    @app.route(pattern, endpoint=endpoint)
    def handle_multiple_urls():
        if 'username' in session:
            return redirect(url_for('dashboard'))
        elif request.path not in url_patterns:
            error_message = "You don't have any active session, please login first"
            return render_template('sign-in.html', error=error_message)
        else:
            return render_template('sign-in.html')



@app.route('/')
def home():
    return render_template('sign-in.html')

@app.route('/assets/<path:filename>')
def serve_static(filename):
    return send_from_directory('C:\\Users\\Dell\\Documents\\6dOps_Git\\6dOps_Git\\app\\assets\\', filename)

@app.route('/static/media/<path:filename>')
def serve_media(filename):
    return send_from_directory('C:\\Users\\Dell\\Documents\\6dOps_Git\\6dOps_Git\\app\\media\\', filename)

@app.route('/index') 
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('sign-in.html')



@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()

    if user and check_password_hash(user['password'], password):
        session['username'] = user['username']
        return redirect(url_for('dashboard'))
    else:
        return render_template('sign-in.html', error='Invalid login credentials')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html')
    else:
        return redirect(url_for('index'))
    
@app.route('/billing')
def billing():
    if 'username' in session:
        return render_template('billing.html')
    else:
        return redirect(url_for('index'))
    
@app.route('/rtl')
def rtl():
    if 'username' in session:
        return render_template('rtl.html')
    else:
        return redirect(url_for('index'))
    
@app.route('/tables')
def tables():
    if 'username' in session:
        return render_template('tables.html')
    else:
        return redirect(url_for('index'))

@app.route('/virtualreality')
def virtualreality():
    if 'username' in session:
        return render_template('virtual-reality.html')
    else:
        return redirect(url_for('index'))


@app.route('/profile')
def profile():
    if 'username' in session:
        return render_template('profile.html')
    else:
        return redirect(url_for('index'))
    
@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)