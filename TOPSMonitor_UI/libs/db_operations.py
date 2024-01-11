# db_operations.py
import mysql.connector
from flask import current_app

def create_db_connection():
    db_config = {
        "host": current_app.config.get("db_host", "127.0.0.1"),
        "user": current_app.config.get("db_user", "opsuser"),
        "port": int(current_app.config.get("db_port", 3307)),
        "password": current_app.config.get("db_password", "opsuser@6Dtech"),
        "database": current_app.config.get("db_database", "OPS")
    }

    return mysql.connector.connect(**db_config)

def execute_query(query):
    connection = create_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    finally:
        cursor.close()
        connection.close()

def execute_query_u(query):
    connection = create_db_connection()
    cursor = connection.cursor(dictionary=True)  # Use dictionary cursor to get results as dictionaries

    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return cursor, connection, result
    except Exception as e:
        print(f"Error executing query: {e}")
        return None, None, []


