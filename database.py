"""database.py - SQLite connection, table creation, and starter data."""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "barangay.db")


class Database:
    def __init__(self, path=DB_PATH):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row          # lets us use row['column_name']
        self.conn.execute("PRAGMA foreign_keys = ON")  # enforce relationships
        self.create_tables()
        self.seed_data()

    # helpers used by the other modules
    def query(self, sql, params=()):
        """SELECT returning a list of rows."""
        return self.conn.execute(sql, params).fetchall()

    def query_one(self, sql, params=()):
        """SELECT returning a single row (or None)."""
        return self.conn.execute(sql, params).fetchone()

    def execute(self, sql, params=()):
        """INSERT/UPDATE/DELETE. Returns the cursor, or None if it failed."""
        try:
            cur = self.conn.execute(sql, params)
            self.conn.commit()
            return cur
        except sqlite3.Error:
            self.conn.rollback()
            return None

    #  schema
    def create_tables(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT NOT NULL UNIQUE,
            password  TEXT NOT NULL,
            role      TEXT NOT NULL CHECK (role IN ('Admin', 'Staff')),
            theme     TEXT NOT NULL DEFAULT 'retro_green'
        );

        CREATE TABLE IF NOT EXISTS residents (
            resident_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name   TEXT NOT NULL,
            birthdate   TEXT NOT NULL,
            address     TEXT,
            contact     TEXT
        );

        CREATE TABLE IF NOT EXISTS certificates (
            cert_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            cert_name TEXT NOT NULL UNIQUE,
            fee       REAL NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS requests (
            request_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            resident_id  INTEGER NOT NULL,
            cert_id      INTEGER NOT NULL,
            request_date TEXT NOT NULL,
            status       TEXT NOT NULL DEFAULT 'Pending'
                         CHECK (status IN ('Pending','Approved','Released','Cancelled')),
            FOREIGN KEY (resident_id) REFERENCES residents(resident_id) ON DELETE CASCADE,
            FOREIGN KEY (cert_id)     REFERENCES certificates(cert_id)  ON DELETE CASCADE
        );
        """)
        self.conn.commit()

    # starter data (only runs on an empty database) 
    def seed_data(self):
        from auth import AuthManager  # local import avoids a circular import

        if self.query_one("SELECT COUNT(*) AS n FROM users")["n"] == 0:
            self.execute("INSERT INTO users (username, password, role, theme) VALUES (?,?,?,?)",
                         ("admin", AuthManager.hash_password("admin123"), "Admin", "retro_green"))
            self.execute("INSERT INTO users (username, password, role, theme) VALUES (?,?,?,?)",
                         ("staff", AuthManager.hash_password("staff123"), "Staff", "retro_green"))

        if self.query_one("SELECT COUNT(*) AS n FROM certificates")["n"] == 0:
            for name, fee in [("Barangay Clearance", 50), ("Certificate of Identity", 30),
                              Certificate(" of Indigency", 0), ("Business Clearance", 200),
                             Certificate(" for financial assistance", 0), ("of Good Moral Character", 50) ,
                             Certificate(" of Residency", 0), ("Non-Residency", 200),
                            Certificate ("Construction or Building Permit", 3000), ("for Events, Gatherings, or Use of Public Space", 1000),
                             Certificate("for fencing or excavation")]:
                self.execute("INSERT INTO certificates (cert_name, fee) VALUES (?,?)", (name, fee))

        if self.query_one("SELECT COUNT(*) AS n FROM residents")["n"] == 0:
            for name, bdate, addr, contact in [
                ("Juan Dela Cruz", "1990-05-14", "Purok 1, Poblacion", "09171234567"),
                ("Maria Santos", "1985-11-02", "Purok 3, Bajumpandan", "09281234567"),
                ("Pedro Reyes", "2000-02-20", "Purok 5, Tinago", "09391234567"),
            ]:
                self.execute("INSERT INTO residents (full_name, birthdate, address, contact) VALUES (?,?,?,?)",
                             (name, bdate, addr, contact))
