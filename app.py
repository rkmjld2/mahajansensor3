from flask import Flask, request, jsonify, render_template
import mysql.connector
import os
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# ---------- DATABASE CONNECTION ----------
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        port=int(os.environ.get("DB_PORT", 4000)),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME"),
        autocommit=True,
    )


# ---------- HOME PAGE ----------
@app.route("/")
def home():
    return render_template("index.html")


# ---------- API TO RECEIVE DATA ----------

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
@app.route("/api/data")
def receive_data():
    key = request.args.get("key")
    server_key = os.environ.get("SECRET_KEY")

    return jsonify({
        "received_key": key,
        "server_key": server_key,
        "match": key == server_key
    })


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


# ---------- API CUSTOM SELECT QUERY (dev only) ----------
import mysql.connector
from datetime import datetime, timezone, timedelta

@app.route("/api/search/query")
def search_by_query():
    try:
        q = request.args.get("q", "").strip()

        if not q:
            return jsonify({"error": "query is empty"})

        lower = q.strip().lower()

        # Only allow SELECT, INSERT, UPDATE, DELETE
        if not (
            lower.startswith("select") or
            lower.startswith("insert") or
            lower.startswith("update") or
            lower.startswith("delete")
        ):
            return jsonify({"error": "only SELECT/INSERT/UPDATE/DELETE allowed"})

        if any(k in lower for k in ("drop ", "truncate ", "create ", "alter ")):
            return jsonify({"error": "schema‑modifying commands blocked"})

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # or without dictionary=True if you prefer

        try:
            cursor.execute(q)

            # If SELECT → fetch ALL results so no "unread result" remains
            if lower.startswith("select"):
                rows = cursor.fetchall()
            else:
                rows = []

        except Exception as e:
            # Always close cursor and connection
            cursor.close()
            conn.close()
            raise e

        conn.commit()  # for non‑SELECT

        cursor.close()
        conn.close()

        # Convert timestamp for display
        for row in rows:
            if "timestamp" in row and row["timestamp"]:
                dt = row["timestamp"].replace(tzinfo=timezone.utc)
                ist = dt + timedelta(hours=5, minutes=30)
                row["timestamp"] = ist.strftime("%d/%m/%Y %H:%M:%S")

        # Return SELECT rows or simple success for others
        if lower.startswith("select"):
            return jsonify(rows)
        else:
            return jsonify({
                "status": "ok",
                "affected_rows": cursor.rowcount,
                "query_type": "non_SELECT"
            })

    except Exception as e:
        print("CUSTOM QUERY ERROR:", e)
        return jsonify({"error": str(e)})
if __name__ == "__main__":
    app.run(debug=True)
