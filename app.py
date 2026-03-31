from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import mysql.connector
import os
from datetime import datetime, timezone, timedelta

load_dotenv()  # Load .env FIRST
app = Flask(__name__)  # MISSING - ADD THIS!

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

# ---------- DEBUG ROUTE (TEMP) ----------
@app.route("/debug")
def debug():
    return {
        "DB_HOST": os.environ.get("DB_HOST"),
        "SECRET_KEY": os.environ.get("SECRET_KEY")[:10] + "..." if os.environ.get("SECRET_KEY") else "MISSING",
        "SECRET_KEY_EXISTS": bool(os.environ.get("SECRET_KEY")),
        "FULL_ENV_VARS": [k for k in os.environ if k.startswith('DB_') or k == 'SECRET_KEY']
    }

# ---------- API TO RECEIVE DATA ----------
@app.route("/api/data")
def receive_data():
    print("DEBUG: SECRET_KEY =", os.environ.get("SECRET_KEY"))  # LOG CHECK
    print("DEBUG: ESP KEY =", request.args.get("key"))
    
    if request.args.get("key") != os.environ.get("SECRET_KEY"):
        print("KEY MISMATCH!")
        return jsonify({"status": "unauthorized"})

    # REST OF YOUR CODE (s1,s2,s3 insert)...
    # [Keep your existing receive_data body]

# [Keep all other routes: home, getdata, search_by_date, search_by_query]

if __name__ == "__main__":
    app.run(debug=True)
