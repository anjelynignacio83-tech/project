"""models.py - database queries for residents, certificates, and requests."""


class ResidentModel:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        return self.db.query("SELECT * FROM residents ORDER BY resident_id")

    def get_by_id(self, rid):
        return self.db.query_one("SELECT * FROM residents WHERE resident_id = ?", (rid,))

    def search(self, keyword):
        like = f"%{keyword}%"
        return self.db.query(
            """SELECT * FROM residents
               WHERE full_name LIKE ? OR address LIKE ? OR CAST(resident_id AS TEXT) = ?
               ORDER BY resident_id""", (like, like, keyword.strip()))

    def create(self, name, birthdate, address, contact):
        return self.db.execute(
            "INSERT INTO residents (full_name, birthdate, address, contact) VALUES (?,?,?,?)",
            (name, birthdate, address, contact)) is not None

    def update(self, rid, name, birthdate, address, contact):
        cur = self.db.execute(
            "UPDATE residents SET full_name=?, birthdate=?, address=?, contact=? WHERE resident_id=?",
            (name, birthdate, address, contact, rid))
        return cur is not None and cur.rowcount > 0

    def delete(self, rid):
        cur = self.db.execute("DELETE FROM residents WHERE resident_id = ?", (rid,))
        return cur is not None and cur.rowcount > 0


class CertificateModel:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        return self.db.query("SELECT * FROM certificates ORDER BY cert_id")

    def get_by_id(self, cid):
        return self.db.query_one("SELECT * FROM certificates WHERE cert_id = ?", (cid,))

    def create(self, name, fee):
        return self.db.execute("INSERT INTO certificates (cert_name, fee) VALUES (?,?)",
                               (name, fee)) is not None

    def update(self, cid, name, fee):
        cur = self.db.execute("UPDATE certificates SET cert_name=?, fee=? WHERE cert_id=?",
                              (name, fee, cid))
        return cur is not None and cur.rowcount > 0

    def delete(self, cid):
        cur = self.db.execute("DELETE FROM certificates WHERE cert_id = ?", (cid,))
        return cur is not None and cur.rowcount > 0


class RequestModel:
    JOIN_SQL = """
        SELECT rq.request_id, rq.request_date, rq.status,
               r.full_name, c.cert_name, c.fee
        FROM requests rq
        JOIN residents r    ON rq.resident_id = r.resident_id
        JOIN certificates c ON rq.cert_id = c.cert_id
    """

    def __init__(self, db):
        self.db = db

    def get_all_joined(self):
        return self.db.query(self.JOIN_SQL + " ORDER BY rq.request_id")

    def filter_requests(self, status=None, date=None, resident_name=None):
        where, params = [], []
        if status:
            where.append("rq.status = ? COLLATE NOCASE")
            params.append(status.strip())
        if date:
            where.append("rq.request_date = ?")
            params.append(date.strip())
        if resident_name:
            where.append("r.full_name LIKE ?")
            params.append(f"%{resident_name.strip()}%")
        sql = self.JOIN_SQL
        if where:
            sql += " WHERE " + " AND ".join(where)
        return self.db.query(sql + " ORDER BY rq.request_id", params)

    def get_by_id(self, req_id):
        return self.db.query_one("SELECT * FROM requests WHERE request_id = ?", (req_id,))

    def create(self, resident_id, cert_id, request_date, status="Pending"):
        return self.db.execute(
            "INSERT INTO requests (resident_id, cert_id, request_date, status) VALUES (?,?,?,?)",
            (resident_id, cert_id, request_date, status)) is not None

    def update_status(self, req_id, status):
        cur = self.db.execute("UPDATE requests SET status = ? WHERE request_id = ?", (status, req_id))
        return cur is not None and cur.rowcount > 0

    def delete(self, req_id):
        cur = self.db.execute("DELETE FROM requests WHERE request_id = ?", (req_id,))
        return cur is not None and cur.rowcount > 0

    def get_dashboard_stats(self):
        q = self.db.query_one
        return {
            "residents": q("SELECT COUNT(*) AS n FROM residents")["n"],
            "certificates": q("SELECT COUNT(*) AS n FROM certificates")["n"],
            "pending": q("SELECT COUNT(*) AS n FROM requests WHERE status='Pending'")["n"],
            "released": q("SELECT COUNT(*) AS n FROM requests WHERE status='Released'")["n"],
        }

    def get_revenue_summary(self):
        return self.db.query("""
            SELECT c.cert_name,
                   COUNT(rq.request_id) AS total_requests,
                   COALESCE(SUM(CASE WHEN rq.status='Released' THEN 1 ELSE 0 END), 0) AS released_count,
                   COALESCE(SUM(CASE WHEN rq.status='Released' THEN c.fee ELSE 0 END), 0.0) AS total_collected
            FROM certificates c
            LEFT JOIN requests rq ON rq.cert_id = c.cert_id
            GROUP BY c.cert_id, c.cert_name
            ORDER BY c.cert_name
        """)
