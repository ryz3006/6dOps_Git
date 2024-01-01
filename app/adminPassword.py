import mysql.connector
from werkzeug.security import generate_password_hash

# Database connection configuration
db = mysql.connector.connect(
    host="127.0.0.1",
    user="opsuser",
    password="opsuser@6Dtech",
    database="OPS"
)

# Replace 'your_admin_password' with the actual password you want to set for the admin user
hashed_password = generate_password_hash('admin@123', method='pbkdf2:sha256')

# Insert the user into the 'users' table
cursor = db.cursor()

# If 'email' is optional and can be NULL
insert_query = "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)"
user_data = ('admin', hashed_password, 'admin@example.com')

# If 'email' is required and you want to provide a default value
# insert_query = "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)"
# user_data = ('admin', hashed_password, 'admin@example.com')

cursor.execute(insert_query, user_data)
db.commit()

print("User 'admin' inserted successfully.")