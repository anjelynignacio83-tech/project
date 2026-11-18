"""auth.py - login, logout, accounts, themes, password changes."""
import hashlib
import hmac
import os


class AuthManager:
    def __init__(self, db):
        self.db = db
        self.current_user = None  

    # password hashing (never store plain text) 
    @staticmethod
    def hash_password(password, salt=None):
        salt = salt or os.urandom(16).hex()
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000).hex()
        return f"{salt}${digest}"

    @staticmethod
    def verify_password(password, stored):
        try:
            salt, _ = stored.split("$")
        except ValueError:
            return False
        return hmac.compare_digest(AuthManager.hash_password(password, salt), stored)

    #  session
    def login(self, username, password):
        row = self.db.query_one("SELECT * FROM users WHERE username = ?", (username,))
        if row and self.verify_password(password, row["password"]):
            self.current_user = {
                "user_id": row["user_id"],
                "username": row["username"],
                "role": row["role"],
                "theme": row["theme"],
            }
            return True
        return False

    def logout(self):
        self.current_user = None

    #  account actions 
    def update_theme(self, theme):
        if not self.current_user:
            return False
        cur = self.db.execute("UPDATE users SET theme = ? WHERE user_id = ?",
                              (theme, self.current_user["user_id"]))
        if cur is not None:
            self.current_user["theme"] = theme
            return True
        return False

    def change_password(self, new_password):
        if not self.current_user:
            return False
        cur = self.db.execute("UPDATE users SET password = ? WHERE user_id = ?",
                              (self.hash_password(new_password), self.current_user["user_id"]))
        return cur is not None

    def get_all_users(self):
        return self.db.query("SELECT user_id, username, role, theme FROM users ORDER BY user_id")

    def create_user(self, username, password, role):
        cur = self.db.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)",
                              (username, self.hash_password(password), role))
        return cur is not None

    def delete_user(self, user_id):
        
        # Cannot delete the account that is currently logged in
        if self.current_user and str(self.current_user["user_id"]) == str(user_id).strip():
            return False
        cur = self.db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        return cur is not None and cur.rowcount > 0