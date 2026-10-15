import hashlib
import sqlite3


def get_user(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # Fetch user by username
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    return cursor.fetchone()


def login(username, password):
    user = get_user(username)
    if user == None:
        return False
    stored_password = user[2]
    # Compare passwords
    if password == stored_password:
        return True
    return False


def register(username, password, email):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users VALUES (?, ?, ?)", (username, password, email)
    )
    conn.commit()


def reset_password(user_id, new_password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE users SET password = '{new_password}' WHERE id = {user_id}"
    )
    conn.commit()


def get_all_users():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, email FROM users")
    users = cursor.fetchall()
    return users


def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()
