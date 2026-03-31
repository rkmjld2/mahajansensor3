from flask import Flask, request, jsonify, render_template
import mysql.connector
import os
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# ---------- DATABASE CONNECTION ----------
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("host"),
        port=int(os.environ.get("port", 4000)),
        user=os.environ.get("user"),
        password=os.environ.get("password"),
        database=os.environ.get("database"),
        autocommit=True,
    )

# ---------- HOME PAGE ----------
@app.route("/")
def home():
    return render_template("index.html")

# ---------- API TO RECEIVE DATA ----------
@app.route("/api/data")
def receive_data():
    try:
        key = request.args.get("key")

        # 🔐 Match with your environment variable name
        if (key or "").strip() != (os.environ.get("secret_key") or "").strip():
            return jsonify({"status": "unauthorized"})

        s1 = request.args.get("s1")
        s2 = request.args.get("s2")
        s3 = request.args.get("s3")

        if not s1 or not s2 or not s3:
            return jsonify({"status": "missing data"})

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO sensor_db (sensor1, sensor2, sensor3, timestamp)
        VALUES (%s, %s, %s, NOW())
        """

        cursor.execute(query, (s1, s2, s3))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "success"})

    except Exception as e:
        print("INSERT ERROR:", e)
        return jsonify({"status": "error", "message": str(e)})

# ---------- API TO FETCH DATA ----------
@app.route("/api/getdata")
def get_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT id, sensor1, sensor2, sensor3, timestamp
        FROM sensor_db
        ORDER BY id DESC
        LIMIT 50
        """

        cursor.execute(query)
        data = cursor.fetchall()

        cursor.close()
        conn.close()

        for row in data:
            if row["timestamp"]:
                dt = row["timestamp"].replace(tzinfo=timezone.utc)
                ist = dt + timedelta(hours=5, minutes=30)
                row["timestamp"] = ist.strftime("%d/%m/%Y %H:%M:%S")

        return jsonify(data)

    except Exception as e:
        print("FETCH ERROR:", e)
        return jsonify([])

# ---------- API SEARCH BY DATE ----------
@app.route("/api/search/date")
def search_by_date():
    try:
        start = request.args.get("start")
        end = request.args.get("end")

        if not start or not end:
            return jsonify([])

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT id, sensor1, sensor2, sensor3, timestamp
        FROM sensor_db
        WHERE timestamp BETWEEN %s AND %s
        ORDER BY id DESC
        LIMIT 50
        """

        cursor.execute(query, (start, end))
        data = cursor.fetchall()

        cursor.close()
        conn.close()

        for row in data:
            if row["timestamp"]:
                dt = row["timestamp"].replace(tzinfo=timezone.utc)
                ist = dt + timedelta(hours=5, minutes=30)
                row["timestamp"] = ist.strftime("%d/%m/%Y %H:%M:%S")

        return jsonify(data)

    except Exception as e:
        print("DATE SEARCH ERROR:", e)
        return jsonify([])

# ---------- API CUSTOM QUERY ----------
@app.route("/api/search/query")
def search_by_query():
    try:
        q = request.args.get("q", "").strip()

        if not q:
            return jsonify({"error": "query is empty"})

        lower = q.lower()

        # Only allow safe queries
        if not (
            lower.startswith("select") or
            lower.startswith("insert") or
            lower.startswith("update") or
            lower.startswith("delete")
        ):
            return jsonify({"error": "only SELECT/INSERT/UPDATE/DELETE allowed"})

        if any(k in lower for k in ("drop ", "truncate ", "create ", "alter ")):
            return jsonify({"error": "dangerous query blocked"})

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(q)

        if lower.startswith("select"):
            rows = cursor.fetchall()
        else:
            rows = []

        conn.commit()

        cursor.close()
        conn.close()

        for row in rows:
            if "timestamp" in row and row["timestamp"]:
                dt = row["timestamp"].replace(tzinfo=timezone.utc)
                ist = dt + timedelta(hours=5, minutes=30)
                row["timestamp"] = ist.strftime("%d/%m/%Y %H:%M:%S")

        if lower.startswith("select"):
            return jsonify(rows)
        else:
            return jsonify({
                "status": "ok",
                "affected_rows": len(rows)
            })

    except Exception as e:
        print("CUSTOM QUERY ERROR:", e)
        return jsonify({"error": str(e)})

# ---------- MAIN ----------
if __name__ == "__main__":
    app.run(debug=True)
