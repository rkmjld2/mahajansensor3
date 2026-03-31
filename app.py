from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import mysql.connector
import os
from datetime import datetime, timezone, timedelta

load_dotenv()
app = Flask(__name__, template_folder='templates')  # FIXED!

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

# ---------- DEBUG ROUTE (NO KEY CHECK) ----------
@app.route("/debug")
def debug():
    return {
        "DB_HOST": os.environ.get("DB_HOST"),
        "SECRET_KEY": os.environ.get("SECRET_KEY")[:8] + "..." if os.environ.get("SECRET_KEY") else "MISSING",
        "SECRET_KEY_EXISTS": bool(os.environ.get("SECRET_KEY"))
    }

# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("index.html")

# ---------- YOUR EXISTING ROUTES (receive_data, getdata, etc.) ----------
@app.route("/api/data")
def receive_data():
    print("ESP KEY:", request.args.get("key"))
    print("SERVER KEY:", os.environ.get("SECRET_KEY"))
    
    if request.args.get("key") != os.environ.get("SECRET_KEY"):
        return jsonify({"status": "unauthorized"})
    
    # Your INSERT code here...
    s1 = request.args.get("s1")
    s2 = request.args.get("s2")
    s3 = request.args.get("s3")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sensor_db (sensor1, sensor2, sensor3, timestamp) VALUES (%s, %s, %s, NOW())", (s1, s2, s3))
    cursor.close()
    conn.close()
    
    return jsonify({"status": "success"})

# [ADD ALL YOUR OTHER ROUTES: getdata, search_by_date, search_by_query]

if __name__ == "__main__":
    app.run(debug=True)
